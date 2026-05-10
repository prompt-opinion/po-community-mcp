"""Owned Prior Auth Workflow MCP deterministic tools."""

from __future__ import annotations

from typing import Any

from .clinical_foundation_mcp import get_chart_summary, get_patient_snapshot
from .fhir_utils import normalize_text
from .workflow_contract import compose_workflow_output, evidence_from_refs, patient_id_from_snapshot


PA_TRIGGERS = {
    "mri",
    "ct",
    "pet",
    "biologic",
    "semaglutide",
    "ozempic",
    "wegovy",
    "humira",
    "enbrel",
    "specialty",
    "genetic test",
    "inpatient",
}


def check_requirement(request: dict[str, Any]) -> dict[str, Any]:
    """Check whether a requested service or medication likely needs PA."""

    text = normalize_text(" ".join(str(request.get(field, "")) for field in ("service", "medication", "procedure", "notes")))
    matched = sorted(trigger for trigger in PA_TRIGGERS if trigger in text)
    required = bool(matched or request.get("payerRequiresAuth"))
    criteria = ["diagnosis-documentation", "medical-necessity"]
    if any(item in text for item in ("medication", "drug", "semaglutide", "ozempic", "wegovy", "humira", "enbrel")):
        criteria.append("step-therapy")
    if any(item in text for item in ("mri", "ct", "pet", "genetic test")):
        criteria.append("recent-conservative-therapy")
    findings = [
        {
            "code": "PRIOR_AUTH_LIKELY_REQUIRED",
            "severity": "medium",
            "message": f"Matched PA triggers: {', '.join(matched)}.",
        }
    ] if required else []
    output = compose_workflow_output(
        agent_name="Prior Auth Agent",
        patient_id=str(request.get("patientId") or "unknown"),
        workflow_step="check_requirement",
        summary="Prior authorization is likely required." if required else "Prior authorization was not indicated by deterministic triggers.",
        findings=findings,
        evidence=[],
        confidence="medium",
        risk_level="medium" if required else "low",
        human_reviewer_role="UM staff",
        work_completed=["checked request text against configured PA triggers", f"criteria selected: {len(criteria if required else [])}"],
        recommended_next_action="Confirm payer and plan-specific policy before submission.",
        blocked_actions=["auto-submit prior authorization"],
    )
    return {
        **output,
        "required": required,
        "matchedTriggers": matched,
        "criteria": criteria if required else [],
        "requiresHumanReview": True,
    }


def match_evidence(requirement: dict[str, Any], snapshot_or_fhir: Any) -> dict[str, Any]:
    """Map patient context to PA criteria."""

    snapshot = _ensure_snapshot(snapshot_or_fhir)
    summary = get_chart_summary(snapshot)
    criteria = requirement.get("criteria", [])
    matches = []
    missing = []
    for criterion in criteria:
        if criterion == "diagnosis-documentation" and snapshot["conditions"]:
            matches.append(_match(criterion, "Condition records available", [item["sourceRef"] for item in snapshot["conditions"]]))
        elif criterion == "step-therapy" and snapshot["medications"]:
            matches.append(_match(criterion, "Medication history available", [item["sourceRef"] for item in snapshot["medications"]]))
        elif criterion == "recent-conservative-therapy" and (snapshot["encounters"] or snapshot["documents"]):
            refs = [item["sourceRef"] for item in snapshot["encounters"] + snapshot["documents"]]
            matches.append(_match(criterion, "Encounter or document history available", refs))
        elif criterion == "medical-necessity" and (summary["problemList"] or summary["recentSignals"]):
            refs = snapshot["sourceRefs"][:10]
            matches.append(_match(criterion, "Clinical context supports medical necessity review", refs))
        else:
            missing.append({"criterion": criterion, "message": "No matching evidence found in provided data."})
    output = compose_workflow_output(
        agent_name="Prior Auth Agent",
        patient_id=patient_id_from_snapshot(snapshot),
        workflow_step="match_evidence",
        summary=f"Matched {len(matches)} criteria and found {len(missing)} evidence gaps.",
        findings=missing,
        evidence=evidence_from_refs([ref for match in matches for ref in match.get("sourceRefs", [])]),
        confidence="medium",
        risk_level="high" if missing else "medium",
        human_reviewer_role="UM staff",
        work_completed=[f"criteria evaluated: {len(criteria)}", f"criteria matched: {len(matches)}", f"missing criteria: {len(missing)}"],
        recommended_next_action="Fill missing documentation before any payer submission.",
        blocked_actions=["auto-submit prior authorization"],
    )
    return {**output, "matches": matches, "missing": missing, "requiresHumanReview": True}


def draft_packet(request: dict[str, Any], requirement: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    """Draft a PA packet structure for human review."""

    output = compose_workflow_output(
        agent_name="Prior Auth Agent",
        patient_id=str(request.get("patientId") or "unknown"),
        workflow_step="draft_packet",
        summary="Drafted prior authorization packet for human review.",
        findings=evidence.get("missing", []),
        evidence=evidence_from_refs([ref for match in evidence.get("matches", []) for ref in match.get("sourceRefs", [])]),
        confidence="medium",
        risk_level="high",
        human_reviewer_role="UM staff",
        work_completed=["assembled request section", "assembled criteria section", "assembled matched evidence", "assembled evidence gaps"],
        recommended_next_action="Reviewer must complete payer-specific form and approve packet.",
        blocked_actions=["auto-submit prior authorization"],
    )
    return {
        **output,
        "title": f"Prior authorization packet: {request.get('service') or request.get('medication') or 'requested item'}",
        "sections": [
            {"name": "Request", "content": request},
            {"name": "Requirement", "content": requirement},
            {"name": "Evidence matched", "content": evidence.get("matches", [])},
            {"name": "Evidence gaps", "content": evidence.get("missing", [])},
            {"name": "Attestation", "content": "Draft only. Clinician review and payer-specific form completion required."},
        ],
        "readyToSubmit": False,
        "requiresHumanReview": True,
    }


def draft_appeal(denial: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    """Draft an appeal outline from denial reasons and matched evidence."""

    reasons = denial.get("reasons") or []
    output = compose_workflow_output(
        agent_name="Prior Auth Agent",
        patient_id=str(denial.get("patientId") or "unknown"),
        workflow_step="draft_appeal",
        summary=f"Drafted appeal outline for {len(reasons)} denial reasons.",
        findings=[{"code": "DENIAL_REASON", "severity": "high", "message": reason} for reason in reasons],
        evidence=evidence_from_refs([ref for match in evidence.get("matches", []) for ref in match.get("sourceRefs", [])]),
        confidence="medium",
        risk_level="high",
        human_reviewer_role="UM staff",
        work_completed=["summarized denial reasons", "attached matched evidence", "listed remaining gaps"],
        recommended_next_action="Clinical reviewer must approve substantive medical necessity arguments.",
        blocked_actions=["auto-submit appeal"],
    )
    return {
        **output,
        "title": "Prior authorization appeal draft",
        "opening": "This appeal requests reconsideration based on the clinical evidence summarized below.",
        "denialReasons": reasons,
        "evidenceSummary": evidence.get("matches", []),
        "remainingGaps": evidence.get("missing", []),
        "closing": "Please review the attached clinical evidence and payer criteria mapping.",
        "readyToSubmit": False,
        "requiresHumanReview": True,
    }


def _ensure_snapshot(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and {"conditions", "medications", "sourceRefs"}.issubset(value.keys()):
        return value
    return get_patient_snapshot(value)


def _match(criterion: str, message: str, refs: list[str]) -> dict[str, Any]:
    return {"criterion": criterion, "message": message, "sourceRefs": refs}
