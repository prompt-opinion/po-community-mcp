"""Owned Care Gap MCP deterministic tools."""

from __future__ import annotations

from datetime import date
from typing import Any

from .clinical_foundation_mcp import get_patient_snapshot
from .fhir_utils import normalize_text
from .workflow_contract import (
    compose_workflow_output,
    evidence_from_refs,
    patient_id_from_snapshot,
    score_workflow_risk,
)


def evaluate_care_gaps(snapshot_or_fhir: Any, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate deterministic care-gap rules with configurable policy hooks."""

    snapshot = _ensure_snapshot(snapshot_or_fhir)
    policy = policy or {}
    conditions = " ".join(item.get("name", "") for item in snapshot.get("conditions", []))
    condition_text = normalize_text(conditions)
    observations = snapshot.get("observations", [])
    immunizations = snapshot.get("immunizations", [])
    gaps = []
    documentation_gaps = []
    exclusions = []
    evaluated = []

    if _has_any(condition_text, {"diabetes", "diabetic"}):
        evaluated.append("diabetes-a1c-monitoring")
        if not _has_observation(observations, {"a1c", "hba1c", "hemoglobin a1c"}):
            gaps.append(_gap("diabetes-a1c-monitoring", "high", "No A1c evidence found for diabetic patient.", snapshot["sourceRefs"]))
        evaluated.append("diabetes-kidney-monitoring")
        if not _has_observation(observations, {"egfr", "creatinine", "urine albumin", "acr"}):
            gaps.append(_gap("diabetes-kidney-monitoring", "medium", "No kidney monitoring evidence found for diabetic patient.", snapshot["sourceRefs"]))

    if _has_any(condition_text, {"hypertension", "high blood pressure"}):
        evaluated.append("hypertension-bp-followup")
        if not _has_observation(observations, {"blood pressure", "systolic", "diastolic", "bp"}):
            gaps.append(_gap("hypertension-bp-followup", "medium", "No recent blood-pressure evidence found.", snapshot["sourceRefs"]))

    age = _age_years(snapshot.get("patient", {}).get("birthDate", ""))
    if age is None:
        documentation_gaps.append(_doc_gap("age-missing", "Patient age could not be determined for age-based measures."))
    elif 45 <= age <= 75:
        evaluated.append("colorectal-cancer-screening")
        if not _has_procedure_or_document(snapshot, {"colonoscopy", "fit", "cologuard", "colorectal"}):
            gaps.append(_gap("colorectal-cancer-screening", "medium", "No colorectal screening evidence found.", snapshot["sourceRefs"]))
    else:
        exclusions.append({"measure": "colorectal-cancer-screening", "reason": "Patient outside configured age range."})

    evaluated.append("influenza-vaccine")
    if not _has_immunization(immunizations, {"influenza", "flu"}):
        documentation_gaps.append(_doc_gap("influenza-vaccine", "No flu vaccine evidence found; external pharmacy data may be incomplete."))

    for configured_gap in policy.get("requiredGaps", []):
        if isinstance(configured_gap, dict):
            gaps.append(_gap(configured_gap.get("measure", "configured-gap"), configured_gap.get("risk", "medium"), configured_gap.get("message", "Configured care gap."), snapshot["sourceRefs"]))

    risk = score_workflow_risk(gaps)
    output = compose_workflow_output(
        agent_name="Care Gap Agent",
        patient_id=patient_id_from_snapshot(snapshot),
        workflow_step="evaluate_care_gaps",
        summary=f"Evaluated {len(evaluated)} measures; found {len(gaps)} likely open gaps and {len(documentation_gaps)} documentation gaps.",
        findings=gaps + documentation_gaps,
        evidence=evidence_from_refs(snapshot["sourceRefs"][:12]),
        confidence="medium" if documentation_gaps else "high",
        risk_level=risk["risk_level"],
        human_reviewer_role="quality team",
        work_completed=[
            f"evaluated measures: {len(evaluated)}",
            f"open gaps: {len(gaps)}",
            f"documentation gaps: {len(documentation_gaps)}",
            f"excluded measures: {len(exclusions)}",
        ],
        recommended_next_action="Review open gaps and convert appropriate items into visit agenda or outreach tasks.",
        blocked_actions=["automatic patient outreach without eligibility and exclusion review"] if gaps else [],
    )
    return {
        **output,
        "evaluatedMeasures": evaluated,
        "openGaps": gaps,
        "documentationGaps": documentation_gaps,
        "excludedMeasures": exclusions,
    }


def prioritize_care_gaps(evaluation: dict[str, Any]) -> dict[str, Any]:
    """Prioritize care gaps by deterministic risk and documentation certainty."""

    gaps = list(evaluation.get("openGaps", []))
    priority = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    ranked = sorted(gaps, key=lambda item: (priority.get(item.get("severity", "medium"), 2), item.get("measure", "")))
    return {
        "prioritizedGaps": ranked,
        "workCompleted": [f"ranked care gaps: {len(ranked)}"],
        "requiresHumanReview": bool(ranked),
    }


def draft_care_gap_tasks(evaluation: dict[str, Any]) -> dict[str, Any]:
    """Draft care-gap tasks without directly sending outreach or orders."""

    tasks = []
    for gap in evaluation.get("openGaps", []):
        tasks.append(
            {
                "type": "care-gap-review",
                "measure": gap.get("measure"),
                "priority": gap.get("severity", "medium"),
                "description": gap.get("message"),
                "status": "draft",
                "requiresHumanApproval": True,
            }
        )
    for gap in evaluation.get("documentationGaps", []):
        tasks.append(
            {
                "type": "documentation-gap-review",
                "measure": gap.get("measure"),
                "priority": "low",
                "description": gap.get("message"),
                "status": "draft",
                "requiresHumanApproval": False,
            }
        )
    return {
        "tasks": tasks,
        "blockedActions": ["automatic outreach", "automatic order placement"],
        "requiresHumanReview": any(task["requiresHumanApproval"] for task in tasks),
    }


def _ensure_snapshot(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and {"conditions", "observations", "sourceRefs"}.issubset(value.keys()):
        return value
    return get_patient_snapshot(value)


def _gap(measure: str, severity: str, message: str, refs: list[str]) -> dict[str, Any]:
    return {
        "measure": measure,
        "severity": severity,
        "risk_level": severity,
        "message": message,
        "sourceRefs": refs[:8],
    }


def _doc_gap(measure: str, message: str) -> dict[str, Any]:
    return {
        "measure": measure,
        "severity": "low",
        "risk_level": "low",
        "message": message,
        "documentationOnly": True,
    }


def _has_any(text: str, needles: set[str]) -> bool:
    return any(needle in text for needle in needles)


def _has_observation(observations: list[dict[str, Any]], names: set[str]) -> bool:
    return any(_has_any(normalize_text(item.get("name", "")), names) for item in observations)


def _has_immunization(immunizations: list[dict[str, Any]], names: set[str]) -> bool:
    return any(_has_any(normalize_text(item.get("vaccine", "")), names) for item in immunizations)


def _has_procedure_or_document(snapshot: dict[str, Any], names: set[str]) -> bool:
    values = []
    values.extend(item.get("code", "") for item in snapshot.get("procedures", []))
    values.extend(item.get("description", "") for item in snapshot.get("documents", []))
    return any(_has_any(normalize_text(value), names) for value in values)


def _age_years(birth_date: str) -> int | None:
    try:
        born = date.fromisoformat(str(birth_date)[:10])
    except ValueError:
        return None
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
