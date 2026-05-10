"""Owned Medication Safety MCP deterministic tools."""

from __future__ import annotations

from typing import Any

from .clinical_foundation_mcp import get_patient_snapshot
from .fhir_utils import normalize_text
from .workflow_contract import compose_workflow_output, evidence_from_refs, patient_id_from_snapshot, score_workflow_risk


NSAIDS = {"ibuprofen", "naproxen", "diclofenac", "ketorolac", "celecoxib"}
ANTICOAGULANTS = {"warfarin", "apixaban", "rivaroxaban", "dabigatran", "heparin", "enoxaparin"}
ACE_ARBS = {"lisinopril", "losartan", "valsartan", "enalapril", "irbesartan"}
POTASSIUM_RAISING = {"potassium", "spironolactone", "eplerenone"}
OPIOIDS = {"morphine", "oxycodone", "hydrocodone", "fentanyl", "tramadol"}
BENZOS = {"alprazolam", "lorazepam", "diazepam", "clonazepam"}
RENAL_RISK_MEDS = {"metformin", "ibuprofen", "naproxen", "ketorolac"}


def review_medications(snapshot_or_fhir: Any) -> dict[str, Any]:
    """Review medications for deterministic safety issues."""

    snapshot = _ensure_snapshot(snapshot_or_fhir)
    issues = []
    issues.extend(_duplicate_medication_issues(snapshot))
    issues.extend(check_interactions(snapshot)["issues"])
    risk = score_workflow_risk(issues)
    output = compose_workflow_output(
        agent_name="Medication Review Agent",
        patient_id=patient_id_from_snapshot(snapshot),
        workflow_step="review_medications",
        summary=f"Checked {len(snapshot['medications'])} medications and found {len(issues)} deterministic safety issues.",
        findings=issues,
        evidence=evidence_from_refs([ref for issue in issues for ref in issue.get("sourceRefs", [])]),
        confidence="medium",
        risk_level=risk["risk_level"],
        human_reviewer_role="pharmacist",
        work_completed=[
            f"active medication records checked: {len(snapshot['medications'])}",
            "duplicate therapy check",
            "allergy conflict check",
            "interaction screen",
            "renal-risk screen",
        ],
        recommended_next_action="Pharmacist or clinician should review before changing therapy.",
        blocked_actions=["auto-discontinue medication", "auto-change therapy"],
    )
    return {
        **output,
        "medicationCount": len(snapshot["medications"]),
        "issueCount": len(issues),
        "issues": issues,
        "requiresHumanReview": True,
    }


def check_interactions(snapshot_or_fhir: Any) -> dict[str, Any]:
    """Check basic drug-drug, drug-allergy, and renal-risk rules."""

    snapshot = _ensure_snapshot(snapshot_or_fhir)
    meds = {_med_key(item.get("name", "")): item for item in snapshot["medications"] if item.get("name")}
    med_names = set(meds)
    issues = []
    issues.extend(_allergy_conflicts(snapshot, med_names))
    if med_names & NSAIDS and med_names & ANTICOAGULANTS:
        issues.append(_issue("high", "NSAID_ANTICOAGULANT", "NSAID plus anticoagulant may increase bleeding risk.", meds, med_names & (NSAIDS | ANTICOAGULANTS)))
    if med_names & ACE_ARBS and med_names & POTASSIUM_RAISING:
        issues.append(_issue("medium", "HYPERKALEMIA_RISK", "ACE/ARB plus potassium-raising therapy may increase hyperkalemia risk.", meds, med_names & (ACE_ARBS | POTASSIUM_RAISING)))
    if med_names & OPIOIDS and med_names & BENZOS:
        issues.append(_issue("high", "SEDATION_STACK", "Opioid plus benzodiazepine may increase sedation and respiratory risk.", meds, med_names & (OPIOIDS | BENZOS)))
    if med_names & RENAL_RISK_MEDS and _low_egfr(snapshot):
        issues.append(_issue("medium", "RENAL_DOSING_REVIEW", "Renal-risk medication found with low eGFR signal.", meds, med_names & RENAL_RISK_MEDS))
    return {"issues": issues, "requiresHumanReview": True}


def suggest_safer_alternatives(review_or_snapshot: Any) -> dict[str, Any]:
    """Suggest review actions for known medication safety issue codes."""

    review = review_or_snapshot if isinstance(review_or_snapshot, dict) and "issues" in review_or_snapshot else review_medications(review_or_snapshot)
    suggestions = []
    for issue in review.get("issues", []):
        code = issue.get("code")
        suggestions.append(
            {
                "issueCode": code,
                "recommendation": _recommendation_for(code),
                "requiresClinicianApproval": True,
            }
        )
    output = compose_workflow_output(
        agent_name="Medication Review Agent",
        patient_id="unknown",
        workflow_step="suggest_safer_alternatives",
        summary=f"Drafted {len(suggestions)} medication safety review suggestions.",
        findings=review.get("issues", []),
        evidence=evidence_from_refs([ref for issue in review.get("issues", []) for ref in issue.get("sourceRefs", [])]),
        confidence="medium",
        risk_level=score_workflow_risk(review.get("issues", []))["risk_level"],
        human_reviewer_role="pharmacist",
        work_completed=[f"suggestions drafted: {len(suggestions)}"],
        recommended_next_action="Use as review prompts only; clinician approval is required before therapy changes.",
        blocked_actions=["auto-change therapy"],
    )
    return {**output, "suggestions": suggestions, "requiresHumanReview": True}


def _ensure_snapshot(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and {"medications", "allergies", "observations"}.issubset(value.keys()):
        return value
    return get_patient_snapshot(value)


def _duplicate_medication_issues(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    seen: dict[str, list[dict[str, Any]]] = {}
    for medication in snapshot["medications"]:
        key = _med_key(medication.get("name", ""))
        if key:
            seen.setdefault(key, []).append(medication)
    return [
        {
            "severity": "medium",
            "code": "DUPLICATE_ACTIVE_MEDICATION",
            "message": f"Multiple active records found for {items[0].get('name')}.",
            "sourceRefs": [item.get("sourceRef", "") for item in items],
        }
        for items in seen.values()
        if len(items) > 1
    ]


def _allergy_conflicts(snapshot: dict[str, Any], med_names: set[str]) -> list[dict[str, Any]]:
    issues = []
    for allergy in snapshot["allergies"]:
        allergy_key = _med_key(allergy.get("substance", ""))
        if not allergy_key:
            continue
        for med_name in med_names:
            if allergy_key in med_name or med_name in allergy_key:
                issues.append(
                    {
                        "severity": "high",
                        "code": "ALLERGY_CONFLICT",
                        "message": f"Medication may conflict with allergy: {allergy.get('substance')}.",
                        "sourceRefs": [allergy.get("sourceRef", "")],
                    }
                )
    return issues


def _issue(severity: str, code: str, message: str, meds: dict[str, dict], matched: set[str]) -> dict[str, Any]:
    return {
        "severity": severity,
        "code": code,
        "message": message,
        "medications": sorted(matched),
        "sourceRefs": [meds[name].get("sourceRef", "") for name in matched if name in meds],
    }


def _low_egfr(snapshot: dict[str, Any]) -> bool:
    for observation in snapshot["observations"]:
        if "egfr" not in normalize_text(observation.get("name", "")):
            continue
        digits = "".join(ch if ch.isdigit() or ch == "." else " " for ch in observation.get("value", ""))
        for part in digits.split():
            try:
                if float(part) < 30:
                    return True
            except ValueError:
                continue
    return False


def _med_key(name: str) -> str:
    text = normalize_text(name)
    for token in text.split():
        if token in NSAIDS | ANTICOAGULANTS | ACE_ARBS | POTASSIUM_RAISING | OPIOIDS | BENZOS | RENAL_RISK_MEDS:
            return token
    return text


def _recommendation_for(code: str) -> str:
    return {
        "DUPLICATE_ACTIVE_MEDICATION": "Reconcile duplicate medication records before acting on the list.",
        "ALLERGY_CONFLICT": "Hold automated recommendation and ask clinician to verify allergy and medication necessity.",
        "NSAID_ANTICOAGULANT": "Consider non-NSAID pain strategy or bleeding-risk mitigation if clinically appropriate.",
        "HYPERKALEMIA_RISK": "Check potassium/renal labs and review whether both therapies are necessary.",
        "SEDATION_STACK": "Review dose, timing, monitoring, and safer alternatives for combined sedating medications.",
        "RENAL_DOSING_REVIEW": "Check renal dosing guidance and recent kidney function before continuing therapy.",
    }.get(code, "Review issue with a licensed clinician before changing therapy.")
