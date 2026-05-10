"""Owned Referral Routing MCP deterministic tools."""

from __future__ import annotations

from typing import Any

from .clinical_foundation_mcp import get_patient_snapshot
from .fhir_utils import normalize_text
from .transition_of_care_mcp import check_referral_readiness
from .workflow_contract import compose_workflow_output, evidence_from_refs, patient_id_from_snapshot


SPECIALTY_RULES = (
    ({"diabetes", "thyroid", "a1c", "endocrine"}, "Endocrinology"),
    ({"kidney", "ckd", "egfr", "renal"}, "Nephrology"),
    ({"chest pain", "heart", "cardiac", "hypertension"}, "Cardiology"),
    ({"cancer", "oncology", "mass", "tumor"}, "Oncology"),
    ({"seizure", "stroke", "neurology", "weakness"}, "Neurology"),
    ({"pregnancy", "obstetric", "maternal"}, "Obstetrics"),
)


def evaluate_referral_need(referral: dict[str, Any], snapshot_or_fhir: Any) -> dict[str, Any]:
    """Evaluate whether a referral draft has enough evidence and likely specialty."""

    snapshot = _ensure_snapshot(snapshot_or_fhir)
    text = _referral_text(referral, snapshot)
    specialty = referral.get("specialty") or _specialty_for(text)
    readiness = check_referral_readiness({**referral, "specialty": specialty}, snapshot)
    duplicates = detect_duplicate_referrals({**referral, "specialty": specialty}, snapshot)
    red_flags = _red_flags(text)
    findings = []
    if not readiness["ready"]:
        findings.append({"code": "REFERRAL_MISSING_CONTEXT", "severity": "medium", "message": "; ".join(readiness["missing"])})
    if duplicates["duplicates"]:
        findings.append({"code": "POSSIBLE_DUPLICATE_REFERRAL", "severity": "medium", "message": "Similar open referral already exists."})
    if red_flags:
        findings.append({"code": "REFERRAL_RED_FLAG", "severity": "critical", "message": ", ".join(red_flags)})
    risk = "critical" if red_flags else ("medium" if findings else "low")
    output = compose_workflow_output(
        agent_name="Referral Agent",
        patient_id=patient_id_from_snapshot(snapshot),
        workflow_step="evaluate_referral_need",
        summary=f"Referral draft targets {specialty or 'unknown specialty'}; ready={readiness['ready']}.",
        findings=findings,
        evidence=evidence_from_refs(readiness.get("supportingRefs", [])),
        confidence="medium" if specialty else "low",
        risk_level=risk,
        human_reviewer_role="referral coordinator" if risk != "critical" else "responsible clinical team",
        work_completed=[
            "checked referral readiness",
            "checked duplicate referrals",
            "selected specialty routing candidate",
        ],
        recommended_next_action="Review referral packet and route only after required clinical approval.",
        blocked_actions=["auto-dispatch referral", "auto-schedule referral"] if risk in {"medium", "high", "critical"} else [],
    )
    return {
        **output,
        "recommendedSpecialty": specialty,
        "ready": readiness["ready"] and not duplicates["duplicates"] and not red_flags,
        "missing": readiness["missing"],
        "duplicates": duplicates["duplicates"],
        "redFlags": red_flags,
    }


def route_referral(referral: dict[str, Any], snapshot_or_fhir: Any, routing_policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Draft a routing decision without dispatching the referral."""

    routing_policy = routing_policy or {}
    evaluation = evaluate_referral_need(referral, snapshot_or_fhir)
    specialty = evaluation["recommendedSpecialty"] or "General review"
    network = routing_policy.get("preferredNetwork", "default-network")
    queue = routing_policy.get("queues", {}).get(specialty, f"{specialty.lower().replace(' ', '-')}-review")
    return {
        "specialty": specialty,
        "network": network,
        "queue": queue,
        "status": "draft",
        "readyToRoute": evaluation["ready"],
        "requiresHumanReview": True,
        "blockedActions": ["send referral", "schedule appointment"],
    }


def detect_duplicate_referrals(referral: dict[str, Any], snapshot_or_fhir: Any) -> dict[str, Any]:
    """Detect likely duplicate referral ServiceRequest records."""

    snapshot = _ensure_snapshot(snapshot_or_fhir)
    target = normalize_text(" ".join(str(referral.get(field, "")) for field in ("specialty", "reason", "code")))
    duplicates = []
    for service_request in snapshot.get("serviceRequests", []):
        haystack = normalize_text(" ".join(str(service_request.get(field, "")) for field in ("code", "reason", "status")))
        if target and any(token in haystack for token in target.split() if len(token) > 4):
            duplicates.append(service_request)
    return {
        "duplicates": duplicates,
        "requiresHumanReview": bool(duplicates),
    }


def _ensure_snapshot(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and {"serviceRequests", "conditions", "sourceRefs"}.issubset(value.keys()):
        return value
    return get_patient_snapshot(value)


def _referral_text(referral: dict[str, Any], snapshot: dict[str, Any]) -> str:
    parts = [str(referral.get("specialty", "")), str(referral.get("reason", "")), str(referral.get("code", ""))]
    parts.extend(item.get("name", "") for item in snapshot.get("conditions", []))
    parts.extend(item.get("name", "") for item in snapshot.get("observations", []))
    return normalize_text(" ".join(parts))


def _specialty_for(text: str) -> str:
    for tokens, specialty in SPECIALTY_RULES:
        if any(token in text for token in tokens):
            return specialty
    return "Primary care review"


def _red_flags(text: str) -> list[str]:
    flags = []
    if "cancer" in text or "tumor" in text:
        flags.append("possible oncology red flag")
    if "stroke" in text or "neurologic emergency" in text:
        flags.append("neurologic emergency language")
    if "pregnancy complication" in text:
        flags.append("pregnancy complication")
    return flags
