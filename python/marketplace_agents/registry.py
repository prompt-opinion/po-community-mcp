"""Registry, classification, and validation logic for Prompt Opinion resources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MarketplaceResource:
    """Normalized view of a marketplace MCP or agent-like resource."""

    id: str
    name: str
    endpoint: str
    description: str
    auth_required: bool
    supports_fhir_context: bool
    publisher_name: str
    tools: tuple[str, ...]
    categories: tuple[str, ...]


@dataclass(frozen=True)
class ValidationFinding:
    """A validation result suitable for CLI or agent output."""

    level: str
    code: str
    message: str


@dataclass(frozen=True)
class CapabilitySummary:
    """Aggregate counts for marketplace planning."""

    total: int
    auth_required: int
    fhir_enabled: int
    public_resources: int
    category_counts: dict[str, int]


CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "chart-summary": (
        "summary",
        "summarize",
        "patient snapshot",
        "patient context",
        "demographics",
        "document",
        "clinical note",
    ),
    "medication-review": (
        "medication",
        "medications",
        "drug",
        "interaction",
        "allergy",
        "polypharmacy",
        "rxnorm",
        "dose",
    ),
    "care-gap": (
        "care gap",
        "gap",
        "screening",
        "immunization",
        "vaccine",
        "quality",
        "follow-up",
        "followup",
    ),
    "lab-vitals-trend": (
        "observation",
        "observations",
        "vital",
        "vitals",
        "lab",
        "labs",
        "trend",
        "glucose",
        "thyroid",
    ),
    "prior-auth": (
        "prior auth",
        "prior authorization",
        "payer",
        "policy",
        "coverage",
        "appeal",
        "medical necessity",
    ),
    "clinical-coding": (
        "icd",
        "icd-10",
        "snomed",
        "cpt",
        "coding",
        "code",
        "codes",
    ),
    "referral": (
        "referral",
        "refer",
        "handoff",
        "care coordination",
        "transition",
    ),
    "patient-education": (
        "education",
        "patient instructions",
        "plain language",
        "discharge",
        "counseling",
        "translate",
    ),
    "scribe-documentation": (
        "scribe",
        "soap",
        "transcript",
        "documentation",
        "note",
        "documentreference",
    ),
    "marketplace-quality": (
        "validate",
        "validator",
        "test",
        "security",
        "audit",
        "rank",
        "recommend",
    ),
}


def load_marketplace_resources(payload: dict[str, Any]) -> list[MarketplaceResource]:
    """Normalize resources from the exported `all-resources.json` payload."""

    resources = payload.get("resources")
    if not isinstance(resources, list):
        raise ValueError("payload.resources must be a list")
    return [normalize_marketplace_resource(item) for item in resources]


def normalize_marketplace_resource(record: dict[str, Any]) -> MarketplaceResource:
    """Return a normalized resource without mutating the source record."""

    tools = record.get("tools") or []
    tool_names = tuple(
        str(tool.get("name", "")).strip()
        for tool in tools
        if isinstance(tool, dict) and str(tool.get("name", "")).strip()
    )
    publisher = record.get("marketplacePublisher") or {}
    name = str(record.get("name", "")).strip()
    description = str(record.get("description", "")).strip()
    endpoint = str(record.get("endpoint", "")).strip()
    categories = classify_resource(record)
    return MarketplaceResource(
        id=str(record.get("id", "")).strip(),
        name=name,
        endpoint=endpoint,
        description=description,
        auth_required=bool(record.get("authRequired")),
        supports_fhir_context=bool(record.get("supportsFhirContext")),
        publisher_name=str(publisher.get("name", "")).strip(),
        tools=tool_names,
        categories=categories,
    )


def classify_resource(record: dict[str, Any]) -> tuple[str, ...]:
    """Classify a resource into workflow categories from text and tool metadata."""

    parts: list[str] = [
        str(record.get("name", "")),
        str(record.get("description", "")),
    ]
    publisher = record.get("marketplacePublisher") or {}
    parts.extend(
        [
            str(publisher.get("name", "")),
            str(publisher.get("tagline", "")),
            str(publisher.get("about", "")),
        ]
    )
    for tool in record.get("tools") or []:
        if isinstance(tool, dict):
            parts.append(str(tool.get("name", "")))
            parts.append(str(tool.get("description", "")))

    haystack = " ".join(parts).lower()
    matches = [
        category
        for category, keywords in CATEGORY_KEYWORDS.items()
        if any(keyword in haystack for keyword in keywords)
    ]
    return tuple(matches) or ("general",)


def summarize_resources(resources: list[MarketplaceResource]) -> CapabilitySummary:
    """Build aggregate counts for a resource collection."""

    category_counts: dict[str, int] = {}
    for resource in resources:
        for category in resource.categories:
            category_counts[category] = category_counts.get(category, 0) + 1
    return CapabilitySummary(
        total=len(resources),
        auth_required=sum(1 for item in resources if item.auth_required),
        fhir_enabled=sum(1 for item in resources if item.supports_fhir_context),
        public_resources=sum(1 for item in resources if not item.auth_required),
        category_counts=dict(sorted(category_counts.items())),
    )


def validate_marketplace_resource(record: dict[str, Any]) -> list[ValidationFinding]:
    """Validate a static marketplace resource record."""

    findings: list[ValidationFinding] = []
    _require_string(record, "id", findings)
    _require_string(record, "name", findings)
    endpoint = _require_string(record, "endpoint", findings)
    _require_string(record, "description", findings)

    if endpoint and not endpoint.startswith(("https://", "http://")):
        findings.append(
            ValidationFinding("error", "endpoint.invalid_scheme", "Endpoint must be http or https.")
        )
    if endpoint and endpoint.startswith("http://"):
        findings.append(
            ValidationFinding("warning", "endpoint.insecure_http", "Endpoint is not HTTPS.")
        )

    if "authRequired" not in record:
        findings.append(
            ValidationFinding("error", "auth.missing", "authRequired must be present.")
        )
    if "supportsFhirContext" not in record:
        findings.append(
            ValidationFinding("error", "fhir.missing", "supportsFhirContext must be present.")
        )

    tools = record.get("tools")
    if not isinstance(tools, list):
        findings.append(ValidationFinding("error", "tools.invalid", "tools must be a list."))
    elif not tools:
        findings.append(
            ValidationFinding("warning", "tools.empty", "Resource declares no tools.")
        )
    else:
        for index, tool in enumerate(tools):
            if not isinstance(tool, dict):
                findings.append(
                    ValidationFinding("error", "tools.item_invalid", f"Tool {index} must be an object.")
                )
                continue
            if not str(tool.get("name", "")).strip():
                findings.append(
                    ValidationFinding("error", "tools.name_missing", f"Tool {index} is missing a name.")
                )
            if not str(tool.get("description", "")).strip():
                findings.append(
                    ValidationFinding(
                        "warning",
                        "tools.description_missing",
                        f"Tool {tool.get('name', index)} is missing a description.",
                    )
                )

    publisher = record.get("marketplacePublisher")
    if not isinstance(publisher, dict):
        findings.append(
            ValidationFinding("warning", "publisher.missing", "marketplacePublisher is missing.")
        )
    elif not str(publisher.get("name", "")).strip():
        findings.append(
            ValidationFinding("warning", "publisher.name_missing", "Publisher name is missing.")
        )

    return findings


def validate_a2a_agent_card(card: dict[str, Any]) -> list[ValidationFinding]:
    """Validate the A2A agent-card fields Prompt Opinion needs."""

    findings: list[ValidationFinding] = []
    _require_string(card, "name", findings)
    _require_string(card, "description", findings)
    _require_string(card, "version", findings)

    interfaces = card.get("supportedInterfaces")
    if not isinstance(interfaces, list) or not interfaces:
        findings.append(
            ValidationFinding(
                "error",
                "a2a.supported_interfaces_missing",
                "supportedInterfaces must contain at least one interface.",
            )
        )
    else:
        for index, interface in enumerate(interfaces):
            if not isinstance(interface, dict):
                findings.append(
                    ValidationFinding(
                        "error",
                        "a2a.interface_invalid",
                        f"supportedInterfaces[{index}] must be an object.",
                    )
                )
                continue
            if not str(interface.get("url", "")).strip():
                findings.append(
                    ValidationFinding(
                        "error",
                        "a2a.interface_url_missing",
                        f"supportedInterfaces[{index}] is missing url.",
                    )
                )
            if interface.get("protocolBinding") != "JSONRPC":
                findings.append(
                    ValidationFinding(
                        "warning",
                        "a2a.protocol_binding",
                        f"supportedInterfaces[{index}] should use JSONRPC.",
                    )
                )
            if not str(interface.get("protocolVersion", "")).strip():
                findings.append(
                    ValidationFinding(
                        "warning",
                        "a2a.protocol_version_missing",
                        f"supportedInterfaces[{index}] is missing protocolVersion.",
                    )
                )

    skills = card.get("skills")
    if not isinstance(skills, list) or not skills:
        findings.append(
            ValidationFinding("warning", "a2a.skills_missing", "Agent card has no skills.")
        )

    capabilities = card.get("capabilities")
    if not isinstance(capabilities, dict):
        findings.append(
            ValidationFinding("warning", "a2a.capabilities_missing", "Capabilities are missing.")
        )
    elif capabilities.get("stateTransitionHistory") is True:
        findings.append(
            ValidationFinding(
                "error",
                "a2a.state_transition_history",
                "stateTransitionHistory must be false for Prompt Opinion compatibility.",
            )
        )

    security = card.get("security")
    schemes = card.get("securitySchemes")
    if security and not schemes:
        findings.append(
            ValidationFinding(
                "error",
                "a2a.security_schemes_missing",
                "security is declared but securitySchemes is missing.",
            )
        )

    if _has_fhir_extension(card):
        scope_findings = _validate_fhir_scopes(card)
        findings.extend(scope_findings)

    return findings


def _validate_fhir_scopes(card: dict[str, Any]) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    extensions = ((card.get("capabilities") or {}).get("extensions") or [])
    for extension in extensions:
        if not isinstance(extension, dict):
            continue
        uri = str(extension.get("uri", "")).lower()
        if "fhir" not in uri:
            continue
        params = extension.get("params") or {}
        scopes = params.get("scopes") if isinstance(params, dict) else None
        if not isinstance(scopes, list) or not scopes:
            findings.append(
                ValidationFinding(
                    "warning",
                    "a2a.fhir_scopes_missing",
                    "FHIR extension should declare SMART/FHIR scopes.",
                )
            )
        break
    return findings


def _has_fhir_extension(card: dict[str, Any]) -> bool:
    extensions = ((card.get("capabilities") or {}).get("extensions") or [])
    return any(isinstance(item, dict) and "fhir" in str(item.get("uri", "")).lower() for item in extensions)


def _require_string(
    record: dict[str, Any], field: str, findings: list[ValidationFinding]
) -> str:
    value = str(record.get(field, "")).strip()
    if not value:
        findings.append(
            ValidationFinding("error", f"{field}.missing", f"{field} is required.")
        )
    return value

