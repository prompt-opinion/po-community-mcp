"""Runtime registry for owned MCP tool functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .care_gap_mcp import draft_care_gap_tasks, evaluate_care_gaps, prioritize_care_gaps
from .clinical_foundation_mcp import get_chart_summary, get_patient_snapshot, get_recent_signals
from .clinical_coding_mcp import identify_documentation_gaps, suggest_code_candidates, suppress_unsupported_codes
from .lab_vitals_trend_mcp import analyze_observation_trends, detect_urgent_observations, recommend_trend_followup
from .medication_safety_mcp import check_interactions, review_medications, suggest_safer_alternatives
from .prior_auth_workflow_mcp import check_requirement, draft_appeal, draft_packet, match_evidence
from .quality_mcp import (
    build_replacement_plan,
    generate_parity_report,
    map_owned_tool_coverage,
    recommend_composite_mcps,
    summarize_marketplace,
    test_endpoint,
    validate_a2a_card,
    validate_listing,
    validate_marketplace_export,
)
from .transition_of_care_mcp import (
    build_discharge_brief,
    check_referral_readiness,
    create_followup_tasks,
    draft_patient_instructions,
)
from .referral_routing_mcp import detect_duplicate_referrals, evaluate_referral_need, route_referral
from .workflow_contract import (
    compose_workflow_output,
    create_audit_event,
    score_workflow_risk,
    validate_workflow_output,
)


@dataclass(frozen=True)
class OwnedTool:
    name: str
    description: str
    input_keys: tuple[str, ...]
    handler: Callable[[dict[str, Any]], dict[str, Any]]
    required_keys: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputKeys": list(self.input_keys),
        }

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                key: {
                    "type": ["object", "array", "string", "number", "boolean", "null"],
                    "description": f"Input value for {key}.",
                }
                for key in self.input_keys
            },
            "required": list(self.required_keys),
            "additionalProperties": True,
        }


def list_owned_tools() -> list[dict[str, Any]]:
    return [tool.to_dict() for tool in OWNED_TOOLS.values()]


def list_owned_mcp_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.input_schema(),
        }
        for tool in OWNED_TOOLS.values()
    ]


def call_owned_tool(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        tool = OWNED_TOOLS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown owned tool: {name}") from exc
    return tool.handler(payload)


def _payload(payload: dict[str, Any]) -> Any:
    return payload.get("payload") or payload.get("fhir") or payload.get("snapshot") or payload


def _snapshot(payload: dict[str, Any]) -> Any:
    return payload.get("snapshot") or payload.get("fhir") or payload.get("payload") or payload


OWNED_TOOLS: dict[str, OwnedTool] = {
    "validate_listing": OwnedTool(
        "validate_listing",
        "Validate one marketplace MCP record.",
        ("record",),
        lambda data: validate_listing(data.get("record", data)),
        ("record",),
    ),
    "validate_marketplace_export": OwnedTool(
        "validate_marketplace_export",
        "Validate every listing in an exported marketplace payload.",
        ("payload",),
        lambda data: validate_marketplace_export(data.get("payload", data)),
        ("payload",),
    ),
    "validate_a2a_card": OwnedTool(
        "validate_a2a_card",
        "Validate one A2A agent card payload.",
        ("card",),
        lambda data: validate_a2a_card(data.get("card", data)),
        ("card",),
    ),
    "test_endpoint": OwnedTool(
        "test_endpoint",
        "Probe one MCP endpoint without sending PHI.",
        ("record", "endpoint", "dryRun", "timeoutSeconds"),
        lambda data: test_endpoint(
            data.get("record", data),
            dry_run=bool(data.get("dryRun", True)),
            timeout_seconds=float(data.get("timeoutSeconds", 5.0)),
        ),
    ),
    "summarize_marketplace": OwnedTool(
        "summarize_marketplace",
        "Summarize marketplace capability coverage.",
        ("payload",),
        lambda data: summarize_marketplace(data.get("payload", data)),
        ("payload",),
    ),
    "recommend_composite_mcps": OwnedTool(
        "recommend_composite_mcps",
        "Rank existing MCPs as benchmarks for owned composites.",
        ("payload", "limit"),
        lambda data: recommend_composite_mcps(data.get("payload", data), limit=int(data.get("limit", 8))),
        ("payload",),
    ),
    "build_replacement_plan": OwnedTool(
        "build_replacement_plan",
        "Build safe replacement readiness plan.",
        ("payload", "limit"),
        lambda data: build_replacement_plan(data.get("payload", data), limit=int(data.get("limit", 5))),
        ("payload",),
    ),
    "generate_parity_report": OwnedTool(
        "generate_parity_report",
        "Generate owned MCP parity report.",
        ("payload", "limit"),
        lambda data: generate_parity_report(data.get("payload", data), limit=int(data.get("limit", 10))),
        ("payload",),
    ),
    "map_owned_tool_coverage": OwnedTool(
        "map_owned_tool_coverage",
        "Map owned tools to marketplace benchmark tools.",
        ("payload", "limit"),
        lambda data: map_owned_tool_coverage(data.get("payload", data), limit=int(data.get("limit", 10))),
        ("payload",),
    ),
    "compose_workflow_output": OwnedTool(
        "compose_workflow_output",
        "Compose the shared clinical workflow output contract.",
        ("payload",),
        lambda data: compose_workflow_output(**data.get("payload", data)),
        ("payload",),
    ),
    "validate_workflow_output": OwnedTool(
        "validate_workflow_output",
        "Validate the shared clinical workflow output contract.",
        ("output",),
        lambda data: validate_workflow_output(data.get("output", data)),
        ("output",),
    ),
    "score_workflow_risk": OwnedTool(
        "score_workflow_risk",
        "Score workflow risk from findings and blocked actions.",
        ("findings", "blockedActions", "urgent"),
        lambda data: score_workflow_risk(data.get("findings", []), data.get("blockedActions", []), bool(data.get("urgent", False))),
    ),
    "create_audit_event": OwnedTool(
        "create_audit_event",
        "Create a PHI-minimized audit event for a workflow output.",
        ("output", "reviewerAction", "overrideReason"),
        lambda data: create_audit_event(
            output=data["output"],
            reviewer_action=data.get("reviewerAction", "pending"),
            override_reason=data.get("overrideReason", ""),
        ),
        ("output",),
    ),
    "get_patient_snapshot": OwnedTool(
        "get_patient_snapshot",
        "Normalize a FHIR payload into a patient snapshot.",
        ("fhir",),
        lambda data: get_patient_snapshot(_payload(data)),
        ("fhir",),
    ),
    "get_chart_summary": OwnedTool(
        "get_chart_summary",
        "Return a clinician-oriented chart summary.",
        ("fhir", "snapshot"),
        lambda data: get_chart_summary(_snapshot(data)),
    ),
    "get_recent_signals": OwnedTool(
        "get_recent_signals",
        "Return recent clinical signals.",
        ("fhir", "snapshot", "limit"),
        lambda data: get_recent_signals(_snapshot(data), limit=int(data.get("limit", 10))),
    ),
    "review_medications": OwnedTool(
        "review_medications",
        "Review active medications for deterministic safety issues.",
        ("fhir", "snapshot"),
        lambda data: review_medications(_snapshot(data)),
    ),
    "check_interactions": OwnedTool(
        "check_interactions",
        "Check deterministic medication interaction rules.",
        ("fhir", "snapshot"),
        lambda data: check_interactions(_snapshot(data)),
    ),
    "suggest_safer_alternatives": OwnedTool(
        "suggest_safer_alternatives",
        "Suggest clinician-review actions for detected medication issues.",
        ("review", "fhir", "snapshot"),
        lambda data: suggest_safer_alternatives(data.get("review") or _snapshot(data)),
    ),
    "evaluate_care_gaps": OwnedTool(
        "evaluate_care_gaps",
        "Evaluate preventive and chronic-care gaps with configurable policy rules.",
        ("fhir", "snapshot", "policy"),
        lambda data: evaluate_care_gaps(_snapshot(data), policy=data.get("policy")),
    ),
    "prioritize_care_gaps": OwnedTool(
        "prioritize_care_gaps",
        "Prioritize evaluated care gaps by risk and certainty.",
        ("evaluation",),
        lambda data: prioritize_care_gaps(data.get("evaluation", data)),
        ("evaluation",),
    ),
    "draft_care_gap_tasks": OwnedTool(
        "draft_care_gap_tasks",
        "Draft care-gap review tasks without direct outreach or orders.",
        ("evaluation",),
        lambda data: draft_care_gap_tasks(data.get("evaluation", data)),
        ("evaluation",),
    ),
    "analyze_observation_trends": OwnedTool(
        "analyze_observation_trends",
        "Analyze lab and vital Observation trends.",
        ("fhir", "snapshot", "limit"),
        lambda data: analyze_observation_trends(_snapshot(data), limit=int(data.get("limit", 20))),
    ),
    "detect_urgent_observations": OwnedTool(
        "detect_urgent_observations",
        "Detect observations crossing urgent thresholds.",
        ("fhir", "snapshot"),
        lambda data: detect_urgent_observations(_snapshot(data)),
    ),
    "recommend_trend_followup": OwnedTool(
        "recommend_trend_followup",
        "Draft follow-up tasks from trend analysis.",
        ("analysis",),
        lambda data: recommend_trend_followup(data.get("analysis", data)),
        ("analysis",),
    ),
    "check_requirement": OwnedTool(
        "check_requirement",
        "Check whether a request likely needs prior authorization.",
        ("request",),
        lambda data: check_requirement(data.get("request", data)),
        ("request",),
    ),
    "match_evidence": OwnedTool(
        "match_evidence",
        "Match patient evidence to prior authorization criteria.",
        ("requirement", "fhir", "snapshot"),
        lambda data: match_evidence(data["requirement"], _snapshot(data)),
        ("requirement",),
    ),
    "draft_packet": OwnedTool(
        "draft_packet",
        "Draft a prior authorization packet.",
        ("request", "requirement", "evidence"),
        lambda data: draft_packet(data["request"], data["requirement"], data["evidence"]),
        ("request", "requirement", "evidence"),
    ),
    "draft_appeal": OwnedTool(
        "draft_appeal",
        "Draft a prior authorization appeal outline.",
        ("denial", "evidence"),
        lambda data: draft_appeal(data["denial"], data["evidence"]),
        ("denial", "evidence"),
    ),
    "suggest_code_candidates": OwnedTool(
        "suggest_code_candidates",
        "Suggest evidence-backed ICD candidates and procedure review candidates.",
        ("fhir", "snapshot", "note", "text"),
        lambda data: suggest_code_candidates(data),
    ),
    "identify_documentation_gaps": OwnedTool(
        "identify_documentation_gaps",
        "Identify documentation gaps that prevent confident coding.",
        ("fhir", "snapshot", "note", "text"),
        lambda data: identify_documentation_gaps(data),
    ),
    "suppress_unsupported_codes": OwnedTool(
        "suppress_unsupported_codes",
        "Suppress code candidates with low confidence or missing evidence.",
        ("candidates",),
        lambda data: suppress_unsupported_codes(data.get("candidates", [])),
        ("candidates",),
    ),
    "build_discharge_brief": OwnedTool(
        "build_discharge_brief",
        "Build a transition-ready handoff.",
        ("fhir", "snapshot"),
        lambda data: build_discharge_brief(_snapshot(data)),
    ),
    "draft_patient_instructions": OwnedTool(
        "draft_patient_instructions",
        "Draft patient-facing transition instructions.",
        ("brief", "readingLevel"),
        lambda data: draft_patient_instructions(data["brief"], reading_level=data.get("readingLevel", "plain-language")),
        ("brief",),
    ),
    "create_followup_tasks": OwnedTool(
        "create_followup_tasks",
        "Create transition follow-up tasks.",
        ("fhir", "snapshot"),
        lambda data: create_followup_tasks(_snapshot(data)),
    ),
    "check_referral_readiness": OwnedTool(
        "check_referral_readiness",
        "Check referral packet readiness.",
        ("referral", "fhir", "snapshot"),
        lambda data: check_referral_readiness(data["referral"], _snapshot(data)),
        ("referral",),
    ),
    "evaluate_referral_need": OwnedTool(
        "evaluate_referral_need",
        "Evaluate referral need, readiness, red flags, and likely specialty.",
        ("referral", "fhir", "snapshot"),
        lambda data: evaluate_referral_need(data["referral"], _snapshot(data)),
        ("referral",),
    ),
    "route_referral": OwnedTool(
        "route_referral",
        "Draft referral routing queue and network selection.",
        ("referral", "fhir", "snapshot", "routingPolicy"),
        lambda data: route_referral(data["referral"], _snapshot(data), routing_policy=data.get("routingPolicy")),
        ("referral",),
    ),
    "detect_duplicate_referrals": OwnedTool(
        "detect_duplicate_referrals",
        "Detect likely duplicate referral ServiceRequest records.",
        ("referral", "fhir", "snapshot"),
        lambda data: detect_duplicate_referrals(data["referral"], _snapshot(data)),
        ("referral",),
    ),
}
