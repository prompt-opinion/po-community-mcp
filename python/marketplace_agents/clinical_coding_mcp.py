"""Owned Clinical Coding MCP deterministic support tools."""

from __future__ import annotations

from typing import Any

from .clinical_foundation_mcp import get_patient_snapshot
from .fhir_utils import normalize_text
from .workflow_contract import compose_workflow_output, evidence_from_refs, patient_id_from_snapshot


ICD_RULES = (
    ("diabetes", "E11.9", "Type 2 diabetes mellitus without complications"),
    ("hypertension", "I10", "Essential hypertension"),
    ("kidney", "N18.9", "Chronic kidney disease, unspecified"),
    ("ckd", "N18.9", "Chronic kidney disease, unspecified"),
    ("asthma", "J45.909", "Unspecified asthma, uncomplicated"),
    ("anticoagulant", "Z79.01", "Long term use of anticoagulants"),
)


def suggest_code_candidates(snapshot_or_context: Any) -> dict[str, Any]:
    """Suggest evidence-backed code candidates for coder review."""

    snapshot = _ensure_snapshot(snapshot_or_context)
    text = _coding_text(snapshot_or_context, snapshot)
    candidates = []
    for token, code, description in ICD_RULES:
        if token in text:
            refs = _refs_for_token(snapshot, token)
            candidates.append(
                {
                    "codeSystem": "ICD-10-CM",
                    "code": code,
                    "description": description,
                    "confidence": "medium" if refs else "low",
                    "sourceRefs": refs,
                    "requiresCoderReview": True,
                }
            )
    procedure_candidates = _procedure_candidates(snapshot)
    result = compose_workflow_output(
        agent_name="Clinical Coding Agent",
        patient_id=patient_id_from_snapshot(snapshot),
        workflow_step="suggest_code_candidates",
        summary=f"Generated {len(candidates)} diagnosis candidates and {len(procedure_candidates)} procedure review candidates.",
        findings=candidates + procedure_candidates,
        evidence=evidence_from_refs([ref for item in candidates for ref in item.get("sourceRefs", [])]),
        confidence="medium" if candidates else "low",
        risk_level="high" if candidates or procedure_candidates else "low",
        human_reviewer_role="coder",
        work_completed=[
            f"conditions reviewed: {len(snapshot.get('conditions', []))}",
            f"documents reviewed: {len(snapshot.get('documents', []))}",
            f"codes proposed: {len(candidates)}",
            f"procedure candidates flagged: {len(procedure_candidates)}",
        ],
        recommended_next_action="Coder must review evidence and licensed code content before claim-affecting use.",
        blocked_actions=["final code submission", "CPT content use outside licensed deployment"],
    )
    return {
        **result,
        "diagnosisCandidates": candidates,
        "procedureCandidates": procedure_candidates,
        "cptLicensingRequired": bool(procedure_candidates),
        "readyToSubmit": False,
    }


def identify_documentation_gaps(snapshot_or_context: Any) -> dict[str, Any]:
    """Identify documentation gaps that prevent confident coding."""

    snapshot = _ensure_snapshot(snapshot_or_context)
    gaps = []
    condition_text = normalize_text(" ".join(item.get("name", "") for item in snapshot.get("conditions", [])))
    if "diabetes" in condition_text and not any("a1c" in normalize_text(item.get("name", "")) for item in snapshot.get("observations", [])):
        gaps.append(_gap("diabetes-control-status", "Diabetes code support lacks recent control-status evidence."))
    if "kidney" in condition_text or "ckd" in condition_text:
        if not any("egfr" in normalize_text(item.get("name", "")) for item in snapshot.get("observations", [])):
            gaps.append(_gap("ckd-stage", "CKD support lacks recent eGFR or stage evidence."))
    if snapshot.get("procedures") and not snapshot.get("documents"):
        gaps.append(_gap("procedure-note-detail", "Procedure candidates require licensed code review and procedure-note detail."))
    return {
        "documentationGaps": gaps,
        "requiresHumanReview": bool(gaps),
        "blockedActions": ["claim-affecting code finalization"] if gaps else [],
    }


def suppress_unsupported_codes(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Suppress candidates that have no evidence references or low confidence."""

    kept = []
    suppressed = []
    for candidate in candidates:
        if candidate.get("sourceRefs") and candidate.get("confidence") != "low":
            kept.append(candidate)
        else:
            suppressed.append({**candidate, "suppressionReason": "Missing evidence references or low confidence."})
    return {
        "keptCandidates": kept,
        "suppressedCandidates": suppressed,
        "requiresCoderReview": bool(kept),
        "readyToSubmit": False,
    }


def _ensure_snapshot(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and {"conditions", "observations", "sourceRefs"}.issubset(value.keys()):
        return value
    if isinstance(value, dict) and "snapshot" in value:
        return value["snapshot"]
    if isinstance(value, dict) and "fhir" in value:
        return get_patient_snapshot(value["fhir"])
    return get_patient_snapshot(value)


def _coding_text(context: Any, snapshot: dict[str, Any]) -> str:
    parts = []
    if isinstance(context, dict):
        parts.append(str(context.get("note", "")))
        parts.append(str(context.get("text", "")))
    parts.extend(item.get("name", "") for item in snapshot.get("conditions", []))
    parts.extend(item.get("name", "") for item in snapshot.get("medications", []))
    parts.extend(item.get("description", "") for item in snapshot.get("documents", []))
    return normalize_text(" ".join(parts))


def _refs_for_token(snapshot: dict[str, Any], token: str) -> list[str]:
    refs = []
    for collection in ("conditions", "medications", "documents"):
        for item in snapshot.get(collection, []):
            haystack = normalize_text(" ".join(str(value) for value in item.values()))
            if token in haystack and item.get("sourceRef"):
                refs.append(item["sourceRef"])
    return refs[:6]


def _procedure_candidates(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    for procedure in snapshot.get("procedures", []):
        candidates.append(
            {
                "codeSystem": "CPT-or-HCPCS",
                "description": procedure.get("code", "procedure"),
                "confidence": "low",
                "sourceRefs": [procedure.get("sourceRef", "")],
                "requiresLicensedTerminology": True,
                "requiresCoderReview": True,
            }
        )
    return candidates


def _gap(code: str, message: str) -> dict[str, Any]:
    return {"code": code, "severity": "medium", "message": message}
