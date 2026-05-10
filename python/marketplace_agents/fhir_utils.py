"""Small FHIR R4 normalization helpers used by owned MCP contracts."""

from __future__ import annotations

from typing import Any


def iter_resources(payload: Any) -> list[dict[str, Any]]:
    """Return FHIR resources from a Bundle, list, single resource, or snapshot-like dict."""

    if not payload:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    if payload.get("resourceType") == "Bundle":
        resources = []
        for entry in payload.get("entry", []):
            if isinstance(entry, dict) and isinstance(entry.get("resource"), dict):
                resources.append(entry["resource"])
        return resources
    if "resources" in payload and isinstance(payload["resources"], list):
        return [item for item in payload["resources"] if isinstance(item, dict)]
    if "resourceType" in payload:
        return [payload]
    return []


def resource_ref(resource: dict[str, Any]) -> str:
    resource_type = str(resource.get("resourceType", "Resource"))
    resource_id = str(resource.get("id", "unknown"))
    return f"{resource_type}/{resource_id}"


def code_text(value: Any) -> str:
    """Extract human-readable text from a FHIR CodeableConcept-like value."""

    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return ""
    if value.get("text"):
        return str(value["text"])
    codings = value.get("coding")
    if isinstance(codings, list):
        for coding in codings:
            if not isinstance(coding, dict):
                continue
            if coding.get("display"):
                return str(coding["display"])
            if coding.get("code"):
                return str(coding["code"])
    return ""


def patient_name(patient: dict[str, Any]) -> str:
    names = patient.get("name")
    if not isinstance(names, list) or not names:
        return ""
    first = names[0] if isinstance(names[0], dict) else {}
    given = first.get("given") if isinstance(first.get("given"), list) else []
    family = first.get("family", "")
    return " ".join(str(part) for part in [*given, family] if part).strip()


def medication_name(resource: dict[str, Any]) -> str:
    for field in ("medicationCodeableConcept", "code"):
        text = code_text(resource.get(field))
        if text:
            return text
    if isinstance(resource.get("medicationReference"), dict):
        return str(resource["medicationReference"].get("display", ""))
    return ""


def observation_value(resource: dict[str, Any]) -> str:
    if isinstance(resource.get("valueQuantity"), dict):
        quantity = resource["valueQuantity"]
        value = quantity.get("value")
        unit = quantity.get("unit") or quantity.get("code") or ""
        return f"{value} {unit}".strip()
    for field in ("valueString", "valueBoolean", "valueInteger", "valueDateTime"):
        if field in resource:
            return str(resource[field])
    if isinstance(resource.get("valueCodeableConcept"), dict):
        return code_text(resource["valueCodeableConcept"])
    return ""


def observation_number(resource: dict[str, Any]) -> float | None:
    quantity = resource.get("valueQuantity")
    if isinstance(quantity, dict):
        try:
            return float(quantity["value"])
        except (KeyError, TypeError, ValueError):
            return None
    return None


def resource_date(resource: dict[str, Any]) -> str:
    for field in ("effectiveDateTime", "authoredOn", "recordedDate", "onsetDateTime", "date", "issued"):
        if resource.get(field):
            return str(resource[field])
    period = resource.get("period")
    if isinstance(period, dict):
        return str(period.get("start") or period.get("end") or "")
    return ""


def normalize_text(value: str) -> str:
    return " ".join(value.lower().replace("-", " ").split())

