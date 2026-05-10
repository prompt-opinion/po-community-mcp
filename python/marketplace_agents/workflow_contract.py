"""Shared clinical workflow output, risk, evidence, and audit helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
REVIEWER_BY_RISK = {
    "low": "workflow owner",
    "medium": "assigned clinical reviewer",
    "high": "named licensed approver",
    "critical": "responsible clinical team",
}


def compose_workflow_output(
    *,
    agent_name: str,
    patient_id: str,
    workflow_step: str,
    summary: str,
    findings: list[dict[str, Any]] | None = None,
    evidence: list[dict[str, Any]] | None = None,
    confidence: str | float = "medium",
    risk_level: str = "medium",
    human_reviewer_role: str | None = None,
    work_completed: list[str] | None = None,
    recommended_next_action: str = "Review drafted output before downstream action.",
    blocked_actions: list[str] | None = None,
    rule_version: str = "clinical-workflow-rules-v1",
    model_version: str = "deterministic",
    source_systems: list[str] | None = None,
) -> dict[str, Any]:
    """Return the common clinical workflow output contract."""

    normalized_risk = normalize_risk(risk_level)
    return {
        "agent_name": agent_name,
        "patient_id": patient_id or "unknown",
        "workflow_step": workflow_step,
        "summary": summary,
        "findings": findings or [],
        "evidence": evidence or [],
        "confidence": confidence,
        "risk_level": normalized_risk,
        "requires_human_approval": normalized_risk in {"medium", "high", "critical"},
        "human_reviewer_role": human_reviewer_role or REVIEWER_BY_RISK[normalized_risk],
        "work_completed": work_completed or [],
        "recommended_next_action": recommended_next_action,
        "blocked_actions": blocked_actions or default_blocked_actions(normalized_risk),
        "audit_metadata": audit_metadata(
            agent_name=agent_name,
            workflow_step=workflow_step,
            rule_version=rule_version,
            model_version=model_version,
            source_systems=source_systems,
        ),
    }


def validate_workflow_output(output: dict[str, Any]) -> dict[str, Any]:
    """Validate the shared clinical workflow output contract."""

    required = [
        "agent_name",
        "patient_id",
        "workflow_step",
        "summary",
        "findings",
        "evidence",
        "confidence",
        "risk_level",
        "requires_human_approval",
        "human_reviewer_role",
        "work_completed",
        "recommended_next_action",
        "blocked_actions",
        "audit_metadata",
    ]
    missing = [field for field in required if field not in output]
    invalid = []
    if output.get("risk_level") not in RISK_ORDER:
        invalid.append("risk_level")
    if not isinstance(output.get("findings", []), list):
        invalid.append("findings")
    if not isinstance(output.get("evidence", []), list):
        invalid.append("evidence")
    return {
        "valid": not missing and not invalid,
        "missing": missing,
        "invalid": invalid,
    }


def score_workflow_risk(
    findings: list[dict[str, Any]] | None = None,
    blocked_actions: list[str] | None = None,
    urgent: bool = False,
) -> dict[str, Any]:
    """Score risk from finding severities and blocked actions."""

    risk = "low"
    reasons = []
    for finding in findings or []:
        severity = normalize_risk(str(finding.get("risk_level") or finding.get("severity") or "low"))
        if RISK_ORDER[severity] > RISK_ORDER[risk]:
            risk = severity
        if severity in {"high", "critical"}:
            reasons.append(finding.get("code") or finding.get("message") or severity)
    if blocked_actions:
        risk = max_risk(risk, "high")
        reasons.append("blocked downstream automation")
    if urgent:
        risk = "critical"
        reasons.append("urgent escalation signal")
    return {
        "risk_level": risk,
        "requires_human_approval": risk in {"medium", "high", "critical"},
        "recommended_reviewer_role": REVIEWER_BY_RISK[risk],
        "reasons": reasons,
    }


def create_audit_event(
    *,
    output: dict[str, Any],
    reviewer_action: str = "pending",
    override_reason: str = "",
) -> dict[str, Any]:
    """Create an audit event without storing PHI-heavy payloads."""

    metadata = output.get("audit_metadata", {})
    return {
        "event_type": "clinical_workflow_agent_run",
        "agent_name": output.get("agent_name", ""),
        "patient_id": output.get("patient_id", "unknown"),
        "workflow_step": output.get("workflow_step", ""),
        "risk_level": output.get("risk_level", "medium"),
        "requires_human_approval": bool(output.get("requires_human_approval", True)),
        "reviewer_action": reviewer_action,
        "override_reason": override_reason,
        "finding_count": len(output.get("findings", [])),
        "evidence_count": len(output.get("evidence", [])),
        "run_id": metadata.get("run_id", ""),
        "timestamp": now_iso(),
    }


def evidence_from_refs(
    refs: list[str] | tuple[str, ...],
    *,
    source_system: str = "FHIR",
    evidence_type: str = "sourceRef",
    timestamp: str = "",
    snippet: str = "",
) -> list[dict[str, Any]]:
    """Convert FHIR sourceRefs into evidence objects."""

    evidence = []
    for ref in refs:
        if not ref:
            continue
        resource_type = str(ref).split("/", 1)[0] if "/" in str(ref) else "Resource"
        evidence.append(
            {
                "source_system": source_system,
                "resource_type": resource_type,
                "source_ref": str(ref),
                "timestamp": timestamp,
                "evidence_span": snippet,
                "evidence_type": evidence_type,
            }
        )
    return evidence


def audit_metadata(
    *,
    agent_name: str,
    workflow_step: str,
    rule_version: str,
    model_version: str,
    source_systems: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "run_id": f"{agent_name}:{workflow_step}:{now_iso()}",
        "run_timestamp": now_iso(),
        "rule_version": rule_version,
        "model_version": model_version,
        "source_systems": source_systems or ["FHIR"],
        "prompt_version": "none",
    }


def patient_id_from_snapshot(snapshot: dict[str, Any]) -> str:
    patient = snapshot.get("patient") or {}
    return str(patient.get("id") or "unknown")


def default_blocked_actions(risk_level: str) -> list[str]:
    if risk_level == "low":
        return []
    if risk_level == "critical":
        return ["autonomous downstream action", "silent queueing without urgent alert"]
    if risk_level == "high":
        return ["autonomous downstream action"]
    return ["final submission without reviewer acknowledgment"]


def normalize_risk(value: str) -> str:
    normalized = str(value).lower().strip()
    if normalized in {"critical", "urgent"}:
        return "critical"
    if normalized in {"high", "severe"}:
        return "high"
    if normalized in {"medium", "moderate", "warning"}:
        return "medium"
    return "low"


def max_risk(left: str, right: str) -> str:
    left_risk = normalize_risk(left)
    right_risk = normalize_risk(right)
    return left_risk if RISK_ORDER[left_risk] >= RISK_ORDER[right_risk] else right_risk


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
