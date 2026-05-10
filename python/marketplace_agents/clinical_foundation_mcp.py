"""Owned Clinical Foundation MCP deterministic tools."""

from __future__ import annotations

from typing import Any

from .fhir_utils import (
    code_text,
    iter_resources,
    medication_name,
    normalize_text,
    observation_value,
    patient_name,
    resource_date,
    resource_ref,
)
from .workflow_contract import compose_workflow_output, evidence_from_refs, patient_id_from_snapshot


def get_patient_snapshot(fhir_payload: Any) -> dict[str, Any]:
    """Return normalized demographics, problems, meds, allergies, encounters, and observations."""

    resources = iter_resources(fhir_payload)
    snapshot: dict[str, Any] = {
        "patient": {},
        "conditions": [],
        "medications": [],
        "allergies": [],
        "observations": [],
        "encounters": [],
        "documents": [],
        "serviceRequests": [],
        "coverage": [],
        "claims": [],
        "dispenses": [],
        "immunizations": [],
        "procedures": [],
        "sourceRefs": [],
    }

    for resource in resources:
        resource_type = resource.get("resourceType")
        ref = resource_ref(resource)
        snapshot["sourceRefs"].append(ref)
        if resource_type == "Patient":
            snapshot["patient"] = {
                "id": resource.get("id", ""),
                "name": patient_name(resource),
                "gender": resource.get("gender", ""),
                "birthDate": resource.get("birthDate", ""),
                "sourceRef": ref,
            }
        elif resource_type == "Condition":
            snapshot["conditions"].append(
                {
                    "name": code_text(resource.get("code")),
                    "clinicalStatus": code_text(resource.get("clinicalStatus")),
                    "verificationStatus": code_text(resource.get("verificationStatus")),
                    "onset": resource.get("onsetDateTime", ""),
                    "sourceRef": ref,
                }
            )
        elif resource_type in {"MedicationRequest", "MedicationStatement"}:
            snapshot["medications"].append(
                {
                    "name": medication_name(resource),
                    "status": resource.get("status", ""),
                    "authoredOn": resource.get("authoredOn", ""),
                    "dosage": _dosage_text(resource),
                    "sourceRef": ref,
                }
            )
        elif resource_type == "AllergyIntolerance":
            snapshot["allergies"].append(
                {
                    "substance": code_text(resource.get("code")),
                    "clinicalStatus": code_text(resource.get("clinicalStatus")),
                    "criticality": resource.get("criticality", ""),
                    "sourceRef": ref,
                }
            )
        elif resource_type == "Observation":
            snapshot["observations"].append(
                {
                    "name": code_text(resource.get("code")),
                    "category": _first_category(resource),
                    "value": observation_value(resource),
                    "date": resource_date(resource),
                    "status": resource.get("status", ""),
                    "sourceRef": ref,
                }
            )
        elif resource_type == "Encounter":
            snapshot["encounters"].append(
                {
                    "type": _first_type(resource),
                    "status": resource.get("status", ""),
                    "date": resource_date(resource),
                    "sourceRef": ref,
                }
            )
        elif resource_type == "DocumentReference":
            snapshot["documents"].append(
                {
                    "type": code_text(resource.get("type")),
                    "status": resource.get("status", ""),
                    "date": resource_date(resource),
                    "description": resource.get("description", ""),
                    "sourceRef": ref,
                }
            )
        elif resource_type == "ServiceRequest":
            snapshot["serviceRequests"].append(
                {
                    "code": code_text(resource.get("code")),
                    "status": resource.get("status", ""),
                    "intent": resource.get("intent", ""),
                    "priority": resource.get("priority", ""),
                    "authoredOn": resource.get("authoredOn", ""),
                    "reason": _reason_text(resource),
                    "sourceRef": ref,
                }
            )
        elif resource_type == "Coverage":
            snapshot["coverage"].append(
                {
                    "status": resource.get("status", ""),
                    "type": code_text(resource.get("type")),
                    "payer": _display_list(resource.get("payor")),
                    "class": _coverage_class(resource),
                    "sourceRef": ref,
                }
            )
        elif resource_type in {"Claim", "ExplanationOfBenefit"}:
            snapshot["claims"].append(
                {
                    "type": code_text(resource.get("type")),
                    "status": resource.get("status", ""),
                    "use": resource.get("use", ""),
                    "outcome": resource.get("outcome", ""),
                    "created": resource.get("created", ""),
                    "sourceRef": ref,
                }
            )
        elif resource_type == "MedicationDispense":
            snapshot["dispenses"].append(
                {
                    "name": medication_name(resource),
                    "status": resource.get("status", ""),
                    "whenHandedOver": resource.get("whenHandedOver", ""),
                    "daysSupply": _quantity_text(resource.get("daysSupply")),
                    "sourceRef": ref,
                }
            )
        elif resource_type == "Immunization":
            snapshot["immunizations"].append(
                {
                    "vaccine": code_text(resource.get("vaccineCode")),
                    "status": resource.get("status", ""),
                    "date": resource.get("occurrenceDateTime", ""),
                    "sourceRef": ref,
                }
            )
        elif resource_type == "Procedure":
            snapshot["procedures"].append(
                {
                    "code": code_text(resource.get("code")),
                    "status": resource.get("status", ""),
                    "date": resource_date(resource),
                    "sourceRef": ref,
                }
            )

    snapshot["counts"] = {
        "conditions": len(snapshot["conditions"]),
        "medications": len(snapshot["medications"]),
        "allergies": len(snapshot["allergies"]),
        "observations": len(snapshot["observations"]),
        "encounters": len(snapshot["encounters"]),
        "documents": len(snapshot["documents"]),
        "serviceRequests": len(snapshot["serviceRequests"]),
        "coverage": len(snapshot["coverage"]),
        "claims": len(snapshot["claims"]),
        "dispenses": len(snapshot["dispenses"]),
        "immunizations": len(snapshot["immunizations"]),
        "procedures": len(snapshot["procedures"]),
    }
    snapshot["dataQuality"] = _data_quality(snapshot)
    return snapshot


def get_chart_summary(fhir_payload_or_snapshot: Any) -> dict[str, Any]:
    """Return a clinician-readable chart summary from FHIR or an existing snapshot."""

    snapshot = _ensure_snapshot(fhir_payload_or_snapshot)
    patient = snapshot["patient"]
    active_conditions = [item["name"] for item in snapshot["conditions"] if item.get("name")]
    active_meds = [item["name"] for item in snapshot["medications"] if item.get("name")]
    allergies = [item["substance"] for item in snapshot["allergies"] if item.get("substance")]
    recent_signals = get_recent_signals(snapshot, limit=5)["signals"]
    findings = [
        {"type": "condition", "message": item, "severity": "low"}
        for item in active_conditions[:10]
    ]
    output = compose_workflow_output(
        agent_name="Chart Summary Agent",
        patient_id=patient_id_from_snapshot(snapshot),
        workflow_step="get_chart_summary",
        summary=f"Summarized {len(active_conditions)} conditions, {len(active_meds)} medications, and {len(recent_signals)} recent signals.",
        findings=findings,
        evidence=evidence_from_refs(snapshot["sourceRefs"][:12]),
        confidence="medium" if snapshot.get("dataQuality") else "high",
        risk_level="medium" if snapshot.get("dataQuality") else "low",
        human_reviewer_role="clinician",
        work_completed=[
            f"conditions summarized: {len(active_conditions)}",
            f"medications summarized: {len(active_meds)}",
            f"allergies summarized: {len(allergies)}",
            f"recent signals reviewed: {len(recent_signals)}",
            f"data quality flags: {len(snapshot.get('dataQuality', []))}",
        ],
        recommended_next_action="Review summary against source chart before using it for care decisions.",
        blocked_actions=["unsupported diagnosis inference", "downstream clinical action without review"],
    )
    return {
        **output,
        "patientLine": _patient_line(patient),
        "problemList": active_conditions,
        "medicationList": active_meds,
        "allergies": allergies or ["No allergies found in provided data"],
        "recentSignals": recent_signals,
        "sourceCounts": snapshot["counts"],
        "requiresHumanReview": True,
    }


def get_recent_signals(fhir_payload_or_snapshot: Any, limit: int = 10) -> dict[str, Any]:
    """Return recent observations, encounters, documents, and medication changes."""

    snapshot = _ensure_snapshot(fhir_payload_or_snapshot)
    signals = []
    for collection, label in (
        ("observations", "observation"),
        ("encounters", "encounter"),
        ("documents", "document"),
        ("serviceRequests", "service-request"),
        ("claims", "claim"),
        ("dispenses", "medication-dispense"),
        ("immunizations", "immunization"),
        ("procedures", "procedure"),
        ("medications", "medication"),
        ("conditions", "condition"),
    ):
        for item in snapshot.get(collection, []):
            signals.append(
                {
                    "type": label,
                    "name": item.get("name") or item.get("type") or item.get("description") or item.get("substance") or item.get("code") or item.get("vaccine"),
                    "value": item.get("value", ""),
                    "date": item.get("date") or item.get("authoredOn") or item.get("created") or item.get("whenHandedOver") or item.get("onset", ""),
                    "sourceRef": item.get("sourceRef", ""),
                }
            )
    signals.sort(key=lambda item: item.get("date") or "", reverse=True)
    return {"signals": signals[: max(limit, 0)], "totalSignals": len(signals)}


def _ensure_snapshot(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and {"patient", "conditions", "medications", "observations"}.issubset(value.keys()):
        return value
    return get_patient_snapshot(value)


def _dosage_text(resource: dict[str, Any]) -> str:
    dosage = resource.get("dosageInstruction")
    if isinstance(dosage, list) and dosage:
        first = dosage[0] if isinstance(dosage[0], dict) else {}
        return str(first.get("text", ""))
    return ""


def _first_category(resource: dict[str, Any]) -> str:
    categories = resource.get("category")
    if isinstance(categories, list) and categories:
        return code_text(categories[0])
    return ""


def _first_type(resource: dict[str, Any]) -> str:
    types = resource.get("type")
    if isinstance(types, list) and types:
        return code_text(types[0])
    return code_text(resource.get("class"))


def _patient_line(patient: dict[str, Any]) -> str:
    parts = [patient.get("name"), patient.get("gender"), patient.get("birthDate")]
    return " | ".join(str(part) for part in parts if part) or "Unknown patient"


def _data_quality(snapshot: dict[str, Any]) -> list[str]:
    notes = []
    if not snapshot["patient"]:
        notes.append("missing-patient-resource")
    if not snapshot["conditions"]:
        notes.append("no-conditions-provided")
    if not snapshot["medications"]:
        notes.append("no-medications-provided")
    if not snapshot["observations"]:
        notes.append("no-observations-provided")
    if len({normalize_text(ref) for ref in snapshot["sourceRefs"]}) != len(snapshot["sourceRefs"]):
        notes.append("duplicate-source-refs")
    return notes


def _reason_text(resource: dict[str, Any]) -> str:
    reasons = resource.get("reasonCode")
    if isinstance(reasons, list) and reasons:
        return "; ".join(code_text(item) for item in reasons if code_text(item))
    references = resource.get("reasonReference")
    if isinstance(references, list) and references:
        return "; ".join(str(item.get("display") or item.get("reference") or "") for item in references if isinstance(item, dict))
    return ""


def _coverage_class(resource: dict[str, Any]) -> list[str]:
    classes = resource.get("class")
    if not isinstance(classes, list):
        return []
    return [str(item.get("value") or item.get("name") or "") for item in classes if isinstance(item, dict)]


def _display_list(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    return [str(item.get("display") or item.get("reference") or "") for item in items if isinstance(item, dict)]


def _quantity_text(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    amount = value.get("value")
    unit = value.get("unit") or value.get("code") or ""
    return f"{amount} {unit}".strip()
