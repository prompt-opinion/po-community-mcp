"""Owned Transition of Care MCP deterministic tools."""

from __future__ import annotations

from typing import Any

from .clinical_foundation_mcp import get_chart_summary, get_patient_snapshot, get_recent_signals
from .workflow_contract import compose_workflow_output, evidence_from_refs, patient_id_from_snapshot


def build_discharge_brief(snapshot_or_fhir: Any) -> dict[str, Any]:
    """Build a transition-ready handoff from patient context."""

    snapshot = _ensure_snapshot(snapshot_or_fhir)
    summary = get_chart_summary(snapshot)
    risks = _handoff_risks(snapshot)
    output = compose_workflow_output(
        agent_name="Transition of Care Agent",
        patient_id=patient_id_from_snapshot(snapshot),
        workflow_step="build_discharge_brief",
        summary=f"Built transition handoff with {len(summary['problemList'])} active problems and {len(risks)} handoff risks.",
        findings=[{"code": risk, "severity": "medium", "message": risk} for risk in risks],
        evidence=evidence_from_refs(snapshot["sourceRefs"][:12]),
        confidence="medium",
        risk_level="medium" if risks else "low",
        human_reviewer_role="clinician",
        work_completed=["summarized problems", "summarized medications", "summarized allergies", "checked transition risks"],
        recommended_next_action="Review handoff before discharge, referral, or patient-facing use.",
        blocked_actions=["auto-discharge instructions without review"],
    )
    return {
        **output,
        "patient": summary["patientLine"],
        "activeProblems": summary["problemList"],
        "medications": summary["medicationList"],
        "allergies": summary["allergies"],
        "recentSignals": get_recent_signals(snapshot, limit=8)["signals"],
        "handoffRisks": risks,
        "requiresHumanReview": True,
    }


def draft_patient_instructions(discharge_brief: dict[str, Any], reading_level: str = "plain-language") -> dict[str, Any]:
    """Draft patient-facing instructions from a discharge brief."""

    problems = discharge_brief.get("activeProblems", [])
    medications = discharge_brief.get("medications", [])
    output = compose_workflow_output(
        agent_name="Patient Education Agent",
        patient_id="unknown",
        workflow_step="draft_patient_instructions",
        summary=f"Drafted patient instructions at {reading_level} reading level.",
        findings=[],
        evidence=[],
        confidence="medium",
        risk_level="medium",
        human_reviewer_role="clinician",
        work_completed=["drafted medication reminder", "drafted follow-up reminder", "drafted urgent-symptom safety language"],
        recommended_next_action="Clinician should review instructions before giving them to the patient.",
        blocked_actions=["send patient instructions without review"],
    )
    return {
        **output,
        "readingLevel": reading_level,
        "instructions": [
            "Review your medication list with your care team before making changes.",
            f"Follow up for these active problems: {', '.join(problems[:5]) or 'none listed'}.",
            f"Bring this medication list to your next visit: {', '.join(medications[:8]) or 'none listed'}.",
            "Seek urgent care for worsening symptoms, chest pain, severe shortness of breath, fainting, or confusion.",
        ],
        "requiresHumanReview": True,
    }


def create_followup_tasks(snapshot_or_fhir: Any) -> dict[str, Any]:
    """Create follow-up tasks from gaps in provided transition context."""

    snapshot = _ensure_snapshot(snapshot_or_fhir)
    tasks = []
    if snapshot["medications"]:
        tasks.append(_task("medication-reconciliation", "Reconcile medications within 48 hours.", "high"))
    if snapshot["conditions"]:
        tasks.append(_task("problem-followup", "Schedule follow-up for active problem list.", "medium"))
    if not snapshot["observations"]:
        tasks.append(_task("missing-recent-observations", "Confirm whether recent vitals/labs are needed.", "medium"))
    if snapshot["documents"]:
        tasks.append(_task("document-review", "Review discharge or referral documents.", "medium"))
    output = compose_workflow_output(
        agent_name="Follow-up Planner Agent",
        patient_id=patient_id_from_snapshot(snapshot),
        workflow_step="create_followup_tasks",
        summary=f"Drafted {len(tasks)} follow-up tasks.",
        findings=[{"code": task["type"], "severity": task["priority"], "message": task["description"]} for task in tasks],
        evidence=evidence_from_refs(snapshot["sourceRefs"][:12]),
        confidence="medium",
        risk_level="medium" if tasks else "low",
        human_reviewer_role="care coordinator",
        work_completed=[f"tasks drafted: {len(tasks)}"],
        recommended_next_action="Review tasks before assigning, ordering, or patient outreach.",
        blocked_actions=["auto-assign clinical tasks without review"],
    )
    return {**output, "tasks": tasks, "requiresHumanReview": True}


def check_referral_readiness(referral: dict[str, Any], snapshot_or_fhir: Any) -> dict[str, Any]:
    """Check whether a referral packet has minimum supporting context."""

    snapshot = _ensure_snapshot(snapshot_or_fhir)
    missing = []
    if not referral.get("specialty"):
        missing.append("specialty")
    if not referral.get("reason") and not snapshot["conditions"]:
        missing.append("referral reason or condition evidence")
    if not snapshot["medications"]:
        missing.append("current medication list")
    if not snapshot["observations"] and not snapshot["documents"]:
        missing.append("recent observations or supporting documents")
    output = compose_workflow_output(
        agent_name="Referral Agent",
        patient_id=patient_id_from_snapshot(snapshot),
        workflow_step="check_referral_readiness",
        summary=f"Referral readiness check complete; ready={not missing}.",
        findings=[{"code": "REFERRAL_MISSING_CONTEXT", "severity": "medium", "message": item} for item in missing],
        evidence=evidence_from_refs(snapshot["sourceRefs"][:12]),
        confidence="medium",
        risk_level="medium" if missing else "low",
        human_reviewer_role="referral coordinator",
        work_completed=["checked specialty", "checked referral reason", "checked medications", "checked supporting observations/documents"],
        recommended_next_action="Complete missing referral context before routing.",
        blocked_actions=["auto-send incomplete referral"] if missing else [],
    )
    return {
        **output,
        "ready": not missing,
        "missing": missing,
        "supportingRefs": snapshot["sourceRefs"][:12],
        "requiresHumanReview": True,
    }


def _ensure_snapshot(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and {"conditions", "medications", "observations"}.issubset(value.keys()):
        return value
    return get_patient_snapshot(value)


def _handoff_risks(snapshot: dict[str, Any]) -> list[str]:
    risks = []
    if snapshot["allergies"]:
        risks.append("allergies-present")
    if len(snapshot["medications"]) >= 8:
        risks.append("polypharmacy")
    if not snapshot["documents"]:
        risks.append("missing-transition-document")
    return risks


def _task(task_type: str, description: str, priority: str) -> dict[str, str]:
    return {"type": task_type, "description": description, "priority": priority}
