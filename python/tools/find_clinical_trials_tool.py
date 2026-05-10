"""
Trajectory.OS — Clinical Trial Finder (Tool 4, "Plan B")
========================================================
When standard care fails (prior-authorization denial, out-of-pocket cost is
prohibitive, or a postpartum patient needs continued medication after her
Medicaid cliff), this tool queries ClinicalTrials.gov for actively recruiting
trials that match the patient's condition + state. Each trial typically
provides study medication and care at no cost to the participant — turning a
"sorry, denied" outcome into a "here's how to still get care" outcome.

Inputs are flexible:
  - `conditionOrMedication` is required (free text — "lisinopril",
    "postpartum depression", "hypertension"). The agent supplies this from
    conversation context.
  - `patientId` is optional. When supplied (or available via SHARP context),
    we use the patient's state for location matching and personalize the
    referral letter.
  - `locationOverride` lets the caller force a specific state if patient
    address is missing.

External API: https://clinicaltrials.gov/api/v2/studies  (no auth required)
"""

import json
import traceback
from typing import Annotated

import httpx
from mcp.server.fastmcp import Context
from pydantic import Field

from fhir_client import FhirClient
from fhir_utilities import get_fhir_context, get_patient_id_if_context_exists
from mcp_utilities import create_text_response

# State-code → full-state-name (for ClinicalTrials.gov location queries which
# expect names, not codes). We mirror the most common 2-letter codes; for any
# unknown code we fall back to the raw value, which ClinicalTrials.gov
# generally treats as a free-text filter.
_STATE_NAME = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}

_CT_GOV_BASE = "https://clinicaltrials.gov/api/v2/studies"
_CT_GOV_LINK_BASE = "https://clinicaltrials.gov/study"
_DEFAULT_MAX_RESULTS = 5
_HTTP_TIMEOUT_SECONDS = 15.0


def _resolve_state_name(state_raw: str | None) -> str | None:
    if not state_raw:
        return None
    s = state_raw.strip()
    if len(s) == 2 and s.upper() in _STATE_NAME:
        return _STATE_NAME[s.upper()]
    return s


async def _resolve_patient_location_and_name(
    ctx: Context | None, patient_id: str | None
) -> tuple[str | None, str | None]:
    """Return (patient_name, state_name) — both Optional. Best-effort."""
    if not patient_id:
        return (None, None)
    fc = get_fhir_context(ctx)
    if not fc:
        return (None, None)
    client = FhirClient(base_url=fc.url, token=fc.token)
    try:
        patient = await client.read(f"Patient/{patient_id}")
    except Exception:  # noqa: BLE001
        return (None, None)
    if not patient:
        return (None, None)
    name_entry = (patient.get("name") or [{}])[0]
    first = (name_entry.get("given") or [""])[0]
    family = name_entry.get("family", "")
    full_name = f"{first} {family}".strip() or None
    addresses = patient.get("address") or []
    state_name: str | None = None
    for addr in addresses:
        st = addr.get("state")
        if st:
            state_name = _resolve_state_name(st)
            break
    return (full_name, state_name)


def _summarize_study(study: dict) -> dict:
    """Extract the demo-friendly fields from a ClinicalTrials.gov study object."""
    proto = study.get("protocolSection", {}) or {}
    ident = proto.get("identificationModule", {}) or {}
    status_mod = proto.get("statusModule", {}) or {}
    sponsor_mod = proto.get("sponsorCollaboratorsModule", {}) or {}
    conditions_mod = proto.get("conditionsModule", {}) or {}
    contacts_mod = proto.get("contactsLocationsModule", {}) or {}
    design_mod = proto.get("designModule", {}) or {}

    nct_id = ident.get("nctId", "")
    locations = contacts_mod.get("locations", []) or []
    # Pull at most 3 location lines for compactness.
    location_lines: list[str] = []
    for loc in locations[:3]:
        city = loc.get("city", "")
        state = loc.get("state", "")
        country = loc.get("country", "")
        facility = loc.get("facility", "")
        pieces = [p for p in [facility, city, state, country] if p]
        if pieces:
            location_lines.append(", ".join(pieces))

    return {
        "nct_id": nct_id,
        "title": ident.get("briefTitle", "(no title)"),
        "official_title": ident.get("officialTitle"),
        "status": status_mod.get("overallStatus"),
        "lead_sponsor": (sponsor_mod.get("leadSponsor") or {}).get("name"),
        "conditions": conditions_mod.get("conditions", []),
        "phase": design_mod.get("phases", []),
        "study_type": design_mod.get("studyType"),
        "locations": location_lines,
        "more_locations_available": max(0, len(locations) - 3),
        "url": f"{_CT_GOV_LINK_BASE}/{nct_id}" if nct_id else None,
    }


def _draft_referral_letter(
    patient_name: str | None,
    state_name: str | None,
    condition_or_med: str,
    top_study: dict | None,
) -> str:
    salutation = f"Dear {patient_name},\n\n" if patient_name else "Dear Patient,\n\n"
    if not top_study:
        return (
            f"{salutation}"
            f"We searched for actively recruiting clinical trials matching '{condition_or_med}'"
            f"{f' in {state_name}' if state_name else ''} but did not find a current match. "
            f"Your care team will continue exploring options.\n\n"
            f"Sincerely,\nYour Care Team — via Trajectory.OS"
        )
    locations_str = "; ".join(top_study.get("locations") or []) or "Multiple sites"
    return (
        f"{salutation}"
        f"You may qualify for the following clinical trial, which typically provides "
        f"study medication and study-related care at NO cost to participants:\n\n"
        f"  Trial: {top_study['title']}\n"
        f"  ClinicalTrials.gov ID: {top_study['nct_id']}\n"
        f"  Status: {top_study.get('status')}\n"
        f"  Sponsor: {top_study.get('lead_sponsor') or 'Listed on ClinicalTrials.gov'}\n"
        f"  Recruiting at: {locations_str}\n"
        f"  More information: {top_study.get('url')}\n\n"
        f"This trial is currently enrolling participants whose clinical profile "
        f"matches '{condition_or_med}'. Please discuss with your provider whether "
        f"enrollment is appropriate — participation can preserve continuity of "
        f"medication and care when standard coverage is denied or expiring.\n\n"
        f"Sincerely,\nYour Care Team — via Trajectory.OS"
    )


async def find_clinical_trials_for_patient(
    conditionOrMedication: Annotated[  # noqa: N803
        str,
        Field(
            description=(
                "The condition or medication to search for. Free text — e.g. "
                "'lisinopril', 'postpartum depression', 'hypertension'. The "
                "agent should extract this from conversation context (denied "
                "medication, diagnosis name, etc.)."
            ),
            min_length=1,
        ),
    ],
    patientId: Annotated[  # noqa: N803
        str | None,
        Field(
            description=(
                "Optional FHIR patient ID. If supplied (or available via "
                "SHARP context), the tool uses the patient's state to filter "
                "trials by location and personalizes the referral letter."
            )
        ),
    ] = None,
    locationOverride: Annotated[  # noqa: N803
        str | None,
        Field(
            description=(
                "Optional state name or 2-letter code to force a location "
                "filter. Useful when the patient has no address on file."
            )
        ),
    ] = None,
    maxResults: Annotated[  # noqa: N803
        int,
        Field(
            description="Maximum number of trials to return (default 5, max 10).",
            ge=1,
            le=10,
        ),
    ] = _DEFAULT_MAX_RESULTS,
    ctx: Context = None,
) -> str:
    """
    Trajectory.OS "Plan B" — find actively recruiting clinical trials that
    match the patient's condition/medication, then draft a referral letter.
    Used when standard coverage is denied, expiring, or insufficient.
    """
    try:
        # ── 1. Resolve patient (best effort)
        if not patientId:
            patientId = get_patient_id_if_context_exists(ctx)
        patient_name, patient_state = await _resolve_patient_location_and_name(
            ctx, patientId
        )

        # Caller-supplied location override beats FHIR address.
        location_filter: str | None = (
            _resolve_state_name(locationOverride) if locationOverride else patient_state
        )

        # ── 2. Build ClinicalTrials.gov v2 request
        params: dict[str, str] = {
            "query.cond": conditionOrMedication,
            "filter.overallStatus": "RECRUITING",
            "pageSize": str(maxResults),
            "format": "json",
        }
        if location_filter:
            params["query.locn"] = location_filter

        # ── 3. Fetch
        try:
            async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_SECONDS) as client:
                response = await client.get(_CT_GOV_BASE, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else "?"
            return create_text_response(
                f"ERROR: ClinicalTrials.gov returned HTTP {status} for query "
                f"'{conditionOrMedication}'"
                + (f" in {location_filter}" if location_filter else "")
                + ". The public API may be rate-limited or temporarily unavailable.",
                is_error=False,
            )
        except httpx.HTTPError as e:
            return create_text_response(
                f"ERROR: Could not reach ClinicalTrials.gov: {e}. Check the "
                "MCP server's outbound network access.",
                is_error=False,
            )

        # ── 4. Summarize results
        studies = payload.get("studies", []) or []
        summarized = [_summarize_study(s) for s in studies]

        # ── 5. Draft referral letter for the top match (if any)
        top = summarized[0] if summarized else None
        referral_letter = _draft_referral_letter(
            patient_name=patient_name,
            state_name=location_filter,
            condition_or_med=conditionOrMedication,
            top_study=top,
        )

        return create_text_response(json.dumps({
            "trajectory_os_clinical_trials": {
                "headline": (
                    f"Found {len(summarized)} actively recruiting trial(s) "
                    f"for '{conditionOrMedication}'"
                    + (f" in {location_filter}" if location_filter else "")
                    + "."
                ),
                "query": {
                    "condition_or_medication": conditionOrMedication,
                    "location_filter": location_filter,
                    "patient_id": patientId,
                    "patient_name": patient_name,
                    "max_results": maxResults,
                    "source": _CT_GOV_BASE,
                },
                "trials": summarized,
                "referral_letter_draft": referral_letter,
                "next_recommended_action": (
                    f"Share the referral letter with the patient and discuss "
                    f"enrollment at NCT {top['nct_id']}." if top
                    else "Broaden the search — try a different condition keyword "
                         "or remove the location filter."
                ),
            }
        }, indent=2))

    except Exception as e:  # noqa: BLE001
        return create_text_response(
            f"ERROR: FindClinicalTrialsForPatient crashed: {type(e).__name__}: {e}\n\n"
            f"Traceback:\n{traceback.format_exc()}",
            is_error=False,
        )
