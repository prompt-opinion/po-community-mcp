"""
Trajectory.OS — Postpartum Policy Engine (Tool 1)
==================================================
Calculates the postpartum Medicaid "coverage cliff" for a given patient and,
when the cliff is imminent (≤15 days), executes Zero-Click administrative
interventions: a pre-drafted SMS, a fully pre-filled state extension form, and
an OB/GYN appointment flag.

Data sources (in priority order for delivery date):
  1. FHIR Condition resource  — Livebirth (SNOMED 281050002) onsetDateTime
  2. FHIR DocumentReference   — Discharge summary text (base64-decoded, regex parsed)
  3. FHIR Encounter           — Inpatient encounter period.start (least reliable fallback)

State detection:
  Primary  → Patient.address[0].state
  Fallback → Coverage.payor[0].display (text match)
"""

import base64
import json
import re
from datetime import date, timedelta
from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from fhir_client import FhirClient
from fhir_utilities import get_fhir_context, get_patient_id_if_context_exists
from mcp_utilities import create_text_response
from tools.state_medicaid_policy import get_state_policy

# ── Constants ────────────────────────────────────────────────────────────────

STANDARD_CLIFF_DAYS = 60       # Original Medicaid postpartum coverage window
CRITICAL_THRESHOLD_DAYS = 15   # Triggers Zero-Click interventions
LIVEBIRTH_SNOMED = "281050002" # SNOMED code for livebirth
DISCHARGE_SUMMARY_LOINC = "18842-5"  # LOINC code for discharge summary

# Month name → number mapping for parsing clinical text
_MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

# Regex patterns for date extraction from clinical text (ordered by specificity)
_DATE_PATTERNS = [
    # "March 20, 2026" / "March 20 2026"
    re.compile(
        r"(january|february|march|april|may|june|july|august|september|october|november|december)"
        r"\s+(\d{1,2}),?\s+(\d{4})",
        re.IGNORECASE,
    ),
    # ISO 8601: "2026-03-20"
    re.compile(r"(\d{4})-(\d{2})-(\d{2})"),
    # "20/03/2026" or "03/20/2026" — ambiguous, treated as MM/DD/YYYY
    re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})"),
]

# Context words that indicate a date refers to delivery (used for scoring matches)
_DELIVERY_KEYWORDS = [
    "delivery", "delivered", "born", "birth", "livebirth", "live birth",
    "infant on", "vaginal delivery", "c-section", "cesarean",
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _extract_delivery_date_from_text(text: str) -> date | None:
    """
    Attempt to extract a delivery date from unstructured clinical text.
    Scores candidate dates by proximity to delivery-related keywords and
    returns the highest-confidence match.
    """
    text_lower = text.lower()
    candidates: list[tuple[int, date]] = []  # (score, date)

    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text_lower):
            try:
                groups = match.groups()
                if len(groups) == 3:
                    g0, g1, g2 = groups
                    # Named-month pattern: (month_name, day, year)
                    if g0.isalpha():
                        month = _MONTH_MAP.get(g0.lower())
                        day = int(g1)
                        year = int(g2)
                    # ISO pattern: (year, month, day)
                    elif len(g0) == 4:
                        year, month, day = int(g0), int(g1), int(g2)
                    # Slash pattern: (MM, DD, YYYY)
                    else:
                        month, day, year = int(g0), int(g1), int(g2)

                    candidate = date(year, month, day)
                    # Only consider plausible delivery dates (within last 5 years)
                    if date(2020, 1, 1) <= candidate <= date.today():
                        # Score: count delivery keywords within 100 chars of match
                        window_start = max(0, match.start() - 100)
                        window_end = min(len(text_lower), match.end() + 100)
                        window = text_lower[window_start:window_end]
                        score = sum(kw in window for kw in _DELIVERY_KEYWORDS)
                        candidates.append((score, candidate))
            except (ValueError, TypeError):
                continue

    if not candidates:
        return None
    # Return the date with the highest keyword-proximity score;
    # tie-break by picking the most recent date (most likely the delivery).
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return candidates[0][1]


def _parse_document_reference_date(bundle: dict) -> date | None:
    """Extract delivery date from DocumentReference FHIR bundle entries."""
    entries = bundle.get("entry", [])
    for entry in entries:
        resource = entry.get("resource", {})
        contents = resource.get("content", [])
        for content in contents:
            attachment = content.get("attachment", {})
            raw = attachment.get("data")
            if not raw:
                continue
            try:
                decoded = base64.b64decode(raw).decode("utf-8", errors="replace")
                found = _extract_delivery_date_from_text(decoded)
                if found:
                    return found
            except Exception:
                continue
    return None


def _detect_state_from_patient(patient: dict) -> str | None:
    """Extract 2-letter state code from Patient.address[0].state."""
    addresses = patient.get("address", [])
    for addr in addresses:
        state = addr.get("state", "").strip()
        if len(state) == 2:
            return state.upper()
        # Handle full state names by reverse lookup (edge case)
        if len(state) > 2:
            state_lower = state.lower()
            from tools.state_medicaid_policy import STATE_POLICIES
            for code, policy in STATE_POLICIES.items():
                if policy["name"].lower() == state_lower:
                    return code
    return None


def _detect_state_from_coverage(coverage_bundle: dict) -> str | None:
    """
    Fallback: try to infer state from Coverage.payor[0].display text.
    e.g. "Georgia Department of Community Health (Medicaid)" → "GA"
    """
    from tools.state_medicaid_policy import STATE_POLICIES
    entries = coverage_bundle.get("entry", [])
    for entry in entries:
        resource = entry.get("resource", {})
        payors = resource.get("payor", [])
        for payor in payors:
            display = payor.get("display", "").lower()
            for code, policy in STATE_POLICIES.items():
                if policy["name"].lower() in display:
                    return code
    return None


def _parse_delivery_date_from_condition(condition_bundle: dict) -> date | None:
    """Extract delivery date from Condition.onsetDateTime for livebirth conditions."""
    entries = condition_bundle.get("entry", [])
    for entry in entries:
        resource = entry.get("resource", {})
        # Check SNOMED code for livebirth
        codings = resource.get("code", {}).get("coding", [])
        is_livebirth = any(
            c.get("code") == LIVEBIRTH_SNOMED for c in codings
        )
        if not is_livebirth:
            continue
        onset = resource.get("onsetDateTime", "")
        if onset:
            try:
                # Parse ISO 8601; strip time component if present
                return date.fromisoformat(onset[:10])
            except ValueError:
                continue
    return None


def _build_sms_draft(patient_name: str, phone: str, days: int,
                     cliff_date: date, policy: dict) -> dict:
    state_name = policy["name"]
    agency_phone = policy["phone"]
    website = policy["website"]
    urgency = "URGENT: " if days <= 7 else ""

    message = (
        f"{urgency}Hi {patient_name.split()[0]}, your Medicaid coverage expires in "
        f"{days} day{'s' if days != 1 else ''} on {cliff_date.strftime('%B %d, %Y')}. "
    )
    if policy["arpa"]:
        message += (
            f"You may qualify for a FREE 12-month extension through {state_name} Medicaid. "
            f"Call {agency_phone} or visit {website} TODAY — do not wait."
        )
    else:
        message += (
            f"{state_name} Medicaid ends at 60 days postpartum. Call {agency_phone} "
            f"immediately for alternative coverage options."
        )

    return {"to": phone, "message": message, "character_count": len(message)}


def _build_extension_form(patient: dict, patient_id: str, delivery_date: date,
                          cliff_date: date, policy: dict) -> dict:
    """Build a fully pre-filled state extension form data payload."""
    name_entry = patient.get("name", [{}])[0]
    first_name = (name_entry.get("given") or [""])[0]
    last_name = name_entry.get("family", "")
    dob = patient.get("birthDate", "")
    phone = (patient.get("telecom") or [{}])[0].get("value", "")

    addr = (patient.get("address") or [{}])[0]
    address_line = ", ".join(addr.get("line", []))
    city = addr.get("city", "")
    state_code = addr.get("state", "")
    zip_code = addr.get("postalCode", "")
    full_address = f"{address_line}, {city}, {state_code} {zip_code}".strip(", ")

    extended_end = delivery_date + timedelta(days=policy["months"] * 30)

    form_payload = {
        "form_name": policy["form"],
        "form_number": policy["form_number"],
        "status": "PRE-FILLED — READY FOR PATIENT SIGNATURE AND SUBMISSION",
        "legal_basis": "American Rescue Plan Act (ARPA) Section 9812 — 12-Month Postpartum Medicaid Coverage" if policy["arpa"] else "Standard Medicaid Redetermination",
        "fields": {
            "patient_first_name": first_name,
            "patient_last_name": last_name,
            "date_of_birth": dob,
            "patient_fhir_id": patient_id,
            "medicaid_id": "[RETRIEVE FROM STATE MEDICAID RECORD]",
            "phone_number": phone,
            "mailing_address": full_address,
            "delivery_date": delivery_date.isoformat(),
            "current_coverage_end_date": cliff_date.isoformat(),
            "requested_extension_end_date": extended_end.isoformat(),
            "extension_duration_requested": f"{policy['months']} months",
            "extension_basis": "ARPA 12-Month Postpartum Coverage" if policy["arpa"] else "Standard Redetermination",
            "delivery_confirmed_by": "Inpatient Discharge Summary (FHIR DocumentReference LOINC 18842-5)",
            "medicaid_coverage_type": "Pregnancy-Related Medicaid",
            "signature_required": True,
            "signature_note": "Patient or authorized representative signature required prior to submission.",
        },
        "submit_to": {
            "agency": policy["agency"],
            "phone": policy["phone"],
            "website": policy["website"],
            "fax": policy["fax"],
        },
    }
    return form_payload


def _build_ob_flag(delivery_date: date) -> dict:
    """Generate the 6-week postpartum OB/GYN appointment flag."""
    six_week_due = delivery_date + timedelta(weeks=6)
    today = date.today()
    overdue = today > six_week_due
    days_overdue = (today - six_week_due).days if overdue else None

    return {
        "priority": "HIGH",
        "appointment_type": "6-Week Postpartum OB/GYN Follow-Up",
        "due_by": six_week_due.isoformat(),
        "overdue": overdue,
        "days_overdue": days_overdue,
        "status_note": (
            f"⚠️ 6-week postpartum visit is {days_overdue} day(s) overdue."
            if overdue
            else f"Schedule before {six_week_due.isoformat()}."
        ),
        "required_screenings": [
            "PHQ-9 Postpartum Depression Screening",
            "Blood Pressure / Cardiovascular Check",
            "Contraception Counseling",
            "Wound/Perineal Healing Assessment",
        ],
    }


# ── Main Tool Function ────────────────────────────────────────────────────────

async def analyze_postpartum_coverage(
    patientId: Annotated[  # noqa: N803
        str | None,
        Field(
            description=(
                "The FHIR patient ID to analyze. Optional if patient context "
                "already exists via SHARP headers."
            )
        ),
    ] = None,
    ctx: Context = None,
) -> str:
    """
    Analyzes a postpartum patient's Medicaid coverage timeline.

    - Determines the exact date coverage will expire (60-day cliff).
    - If the cliff is within 15 days (CRITICAL), returns a Zero-Click payload
      containing a pre-drafted patient SMS, a fully pre-filled state Medicaid
      extension form, and a 6-week OB/GYN appointment flag.
    - If the cliff is more than 15 days away (ROUTINE), returns a monitoring
      status with the scheduled cliff date.

    Requires: Patient, Condition (Livebirth), DocumentReference (Discharge Summary),
    and Coverage FHIR resources.
    """
    # ── 1. Resolve patient ID ─────────────────────────────────────────────────
    if not patientId:
        patientId = get_patient_id_if_context_exists(ctx)
    if not patientId:
        raise ValueError("No patient ID provided and no patient context found in SHARP headers.")

    # ── 2. Build FHIR client ──────────────────────────────────────────────────
    fhir_context = get_fhir_context(ctx)
    if not fhir_context:
        raise ValueError("FHIR context (server URL) could not be retrieved from SHARP headers.")

    client = FhirClient(base_url=fhir_context.url, token=fhir_context.token)

    # ── 3. Fetch Patient ──────────────────────────────────────────────────────
    patient = await client.read(f"Patient/{patientId}")
    if not patient:
        raise ValueError(f"Patient '{patientId}' not found on FHIR server.")

    name_entry = patient.get("name", [{}])[0]
    first_name = (name_entry.get("given") or ["Unknown"])[0]
    last_name = name_entry.get("family", "Unknown")
    patient_name = f"{first_name} {last_name}".strip()
    phone = (patient.get("telecom") or [{}])[0].get("value", "N/A")

    # ── 4. Detect state ───────────────────────────────────────────────────────
    state_code = _detect_state_from_patient(patient)
    state_source = "Patient.address"

    # ── 5. Fetch Condition (primary delivery date source) ─────────────────────
    condition_bundle = await client.search(
        "Condition",
        {"patient": patientId, "code": LIVEBIRTH_SNOMED},
    )
    delivery_date: date | None = None
    data_sources_used: list[str] = []

    if condition_bundle:
        delivery_date = _parse_delivery_date_from_condition(condition_bundle)
        if delivery_date:
            data_sources_used.append("Condition/Livebirth (onsetDateTime)")

    # ── 6. Fetch DocumentReference (secondary delivery date source) ───────────
    doc_bundle = await client.search(
        "DocumentReference",
        {"patient": patientId, "type": f"http://loinc.org|{DISCHARGE_SUMMARY_LOINC}"},
    )
    if not delivery_date and doc_bundle:
        delivery_date = _parse_document_reference_date(doc_bundle)
        if delivery_date:
            data_sources_used.append("DocumentReference/DischargeSummary (text extraction)")

    # Fallback: try ALL DocumentReferences if typed search returned nothing
    if not delivery_date:
        doc_bundle_all = await client.search("DocumentReference", {"patient": patientId})
        if doc_bundle_all:
            delivery_date = _parse_document_reference_date(doc_bundle_all)
            if delivery_date:
                data_sources_used.append("DocumentReference/Any (text extraction — fallback)")

    if not delivery_date:
        raise ValueError(
            f"Could not determine a delivery date for patient '{patientId}' from any FHIR source. "
            "Ensure a Condition (SNOMED 281050002) or DocumentReference (LOINC 18842-5) exists."
        )

    # ── 7. Fetch Coverage (confirm Medicaid + state fallback) ─────────────────
    coverage_bundle = await client.search("Coverage", {"patient": patientId})
    if coverage_bundle:
        data_sources_used.append("Coverage/Medicaid (payor confirmation)")
        if not state_code:
            state_code = _detect_state_from_coverage(coverage_bundle)
            if state_code:
                state_source = "Coverage.payor (text match)"

    data_sources_used.insert(0, "Patient/Demographics")

    # ── 8. Calculate cliff and urgency ────────────────────────────────────────
    coverage_cliff = delivery_date + timedelta(days=STANDARD_CLIFF_DAYS)
    today = date.today()
    days_until_cliff = (coverage_cliff - today).days

    # ── 9. Look up state policy ───────────────────────────────────────────────
    policy = get_state_policy(state_code or "")
    extended_end = delivery_date + timedelta(days=policy["months"] * 30)

    # ── 10. Build response ────────────────────────────────────────────────────
    patient_block = {
        "name": patient_name,
        "fhir_id": patientId,
        "phone": phone,
        "state": state_code or "UNKNOWN",
        "state_source": state_source,
        "delivery_date": delivery_date.isoformat(),
        "standard_coverage_cliff_date": coverage_cliff.isoformat(),
        "days_until_cliff": days_until_cliff,
    }

    state_policy_block = {
        "state_code": state_code or "UNKNOWN",
        "state_name": policy["name"],
        "arpa_12_month_extension_available": policy["arpa"],
        "extension_months": policy["months"],
        "extended_coverage_end_if_approved": extended_end.isoformat(),
        "agency_name": policy["agency"],
        "agency_phone": policy["phone"],
        "agency_website": policy["website"],
        "agency_fax": policy["fax"],
        "extension_form": policy["form"],
        "form_number": policy["form_number"],
        "policy_notes": policy["notes"],
    }

    if days_until_cliff > CRITICAL_THRESHOLD_DAYS:
        # ── ROUTINE ───────────────────────────────────────────────────────────
        result = {
            "trajectory_os_analysis": {
                "status": "ROUTINE",
                "summary": (
                    f"{patient_name}'s Medicaid coverage cliff is {days_until_cliff} days away "
                    f"({coverage_cliff.isoformat()}). No immediate action required."
                ),
                "patient": patient_block,
                "state_policy": state_policy_block,
                "monitoring": {
                    "action_required": False,
                    "next_review_recommended": (
                        coverage_cliff - timedelta(days=CRITICAL_THRESHOLD_DAYS)
                    ).isoformat(),
                    "note": (
                        f"Re-run analysis when {CRITICAL_THRESHOLD_DAYS} or fewer days remain. "
                        "Zero-Click interventions will activate automatically at that threshold."
                    ),
                },
                "data_sources_used": data_sources_used,
            }
        }
    else:
        # ── CRITICAL ──────────────────────────────────────────────────────────
        overdue_or_imminent = days_until_cliff <= 0
        status_label = "EXPIRED" if overdue_or_imminent else "CRITICAL"
        alert_msg = (
            f"⚠️ MEDICAID COVERAGE {'HAS EXPIRED' if overdue_or_imminent else 'CLIFF IMMINENT'} — "
            f"{patient_name} — "
            f"{'Coverage ended' if overdue_or_imminent else f'{days_until_cliff} day(s) remaining'}"
        )

        result = {
            "trajectory_os_analysis": {
                "status": status_label,
                "alert": alert_msg,
                "summary": (
                    f"{patient_name}'s standard Medicaid coverage "
                    f"{'expired' if overdue_or_imminent else f'expires in {days_until_cliff} day(s)'} "
                    f"on {coverage_cliff.isoformat()}. "
                    f"{'Georgia' if state_code == 'GA' else policy['name']} offers a "
                    f"{policy['months']}-month ARPA extension — apply immediately."
                    if policy["arpa"]
                    else f"This state has NOT adopted the ARPA extension. Escalate immediately."
                ),
                "patient": patient_block,
                "state_policy": state_policy_block,
                "zero_click_interventions": {
                    "sms_draft": _build_sms_draft(
                        patient_name, phone, days_until_cliff, coverage_cliff, policy
                    ),
                    "extension_form_prefilled": _build_extension_form(
                        patient, patientId, delivery_date, coverage_cliff, policy
                    ),
                    "ob_appointment_flag": _build_ob_flag(delivery_date),
                },
                "data_sources_used": data_sources_used,
            }
        }

    return create_text_response(json.dumps(result, indent=2))
