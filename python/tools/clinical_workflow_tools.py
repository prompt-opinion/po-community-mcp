import json
from typing import Annotated, Any

from mcp.server.fastmcp import Context
from pydantic import Field

from fhir_client import FhirClient
from fhir_utilities import get_fhir_context, get_patient_id_if_context_exists
from marketplace_agents.care_gap_mcp import draft_care_gap_tasks, evaluate_care_gaps, prioritize_care_gaps
from marketplace_agents.clinical_coding_mcp import (
    identify_documentation_gaps,
    suggest_code_candidates,
    suppress_unsupported_codes,
)
from marketplace_agents.clinical_foundation_mcp import (
    get_chart_summary,
    get_patient_snapshot,
)
from marketplace_agents.lab_vitals_trend_mcp import (
    analyze_observation_trends,
    detect_urgent_observations,
    recommend_trend_followup,
)
from marketplace_agents.medication_safety_mcp import (
    review_medications,
    suggest_safer_alternatives,
)
from marketplace_agents.owned_tool_registry import call_owned_tool, list_owned_tools
from marketplace_agents.prior_auth_workflow_mcp import (
    check_requirement,
    draft_appeal,
    draft_packet,
    match_evidence,
)
from marketplace_agents.referral_routing_mcp import (
    detect_duplicate_referrals,
    evaluate_referral_need,
    route_referral,
)
from marketplace_agents.transition_of_care_mcp import (
    build_discharge_brief,
    check_referral_readiness,
    create_followup_tasks,
    draft_patient_instructions,
)
from marketplace_agents.workflow_contract import (
    create_audit_event,
    score_workflow_risk,
    validate_workflow_output,
)
from mcp_utilities import create_text_response


FHIR_RESOURCE_TYPES = (
    "Condition",
    "MedicationRequest",
    "MedicationStatement",
    "MedicationDispense",
    "AllergyIntolerance",
    "Observation",
    "Encounter",
    "ServiceRequest",
    "Coverage",
    "Claim",
    "ExplanationOfBenefit",
    "Immunization",
    "Procedure",
    "DocumentReference",
)


async def list_owned_clinical_workflow_tools() -> str:
    return _json_response({"tools": list_owned_tools()})


async def call_owned_clinical_workflow_tool(
    toolName: Annotated[str, Field(description="The owned clinical workflow tool name to call.")],  # noqa: N803
    payload: Annotated[dict[str, Any], Field(description="JSON payload for the selected tool.")],
) -> str:
    return _json_response(call_owned_tool(toolName, payload))


async def get_clinical_patient_snapshot(
    patientId: Annotated[str | None, Field(description="Patient id. Optional when patient context exists.")] = None,  # noqa: N803
    fhirPayload: Annotated[dict[str, Any] | None, Field(description="Optional FHIR Bundle or resource payload.")] = None,  # noqa: N803
    ctx: Context = None,
) -> str:
    bundle = await _fhir_payload_or_context_bundle(ctx, patientId, fhirPayload)
    return _json_response(get_patient_snapshot(bundle))


async def get_clinical_chart_summary(
    patientId: Annotated[str | None, Field(description="Patient id. Optional when patient context exists.")] = None,  # noqa: N803
    fhirPayload: Annotated[dict[str, Any] | None, Field(description="Optional FHIR Bundle or resource payload.")] = None,  # noqa: N803
    ctx: Context = None,
) -> str:
    bundle = await _fhir_payload_or_context_bundle(ctx, patientId, fhirPayload)
    return _json_response(get_chart_summary(bundle))


async def review_clinical_medications(
    patientId: Annotated[str | None, Field(description="Patient id. Optional when patient context exists.")] = None,  # noqa: N803
    fhirPayload: Annotated[dict[str, Any] | None, Field(description="Optional FHIR Bundle or resource payload.")] = None,  # noqa: N803
    ctx: Context = None,
) -> str:
    bundle = await _fhir_payload_or_context_bundle(ctx, patientId, fhirPayload)
    return _json_response(review_medications(bundle))


async def suggest_medication_review_actions(
    review: Annotated[dict[str, Any], Field(description="Medication review output or patient snapshot.")],
) -> str:
    return _json_response(suggest_safer_alternatives(review))


async def evaluate_patient_care_gaps(
    patientId: Annotated[str | None, Field(description="Patient id. Optional when patient context exists.")] = None,  # noqa: N803
    fhirPayload: Annotated[dict[str, Any] | None, Field(description="Optional FHIR Bundle or resource payload.")] = None,  # noqa: N803
    policy: Annotated[dict[str, Any] | None, Field(description="Optional local care-gap policy overrides.")] = None,
    ctx: Context = None,
) -> str:
    bundle = await _fhir_payload_or_context_bundle(ctx, patientId, fhirPayload)
    return _json_response(evaluate_care_gaps(bundle, policy=policy))


async def prioritize_patient_care_gaps(
    evaluation: Annotated[dict[str, Any], Field(description="Care gap evaluation output.")],
) -> str:
    return _json_response(prioritize_care_gaps(evaluation))


async def draft_patient_care_gap_tasks(
    evaluation: Annotated[dict[str, Any], Field(description="Care gap evaluation output.")],
) -> str:
    return _json_response(draft_care_gap_tasks(evaluation))


async def analyze_patient_lab_vitals_trends(
    patientId: Annotated[str | None, Field(description="Patient id. Optional when patient context exists.")] = None,  # noqa: N803
    fhirPayload: Annotated[dict[str, Any] | None, Field(description="Optional FHIR Bundle or resource payload.")] = None,  # noqa: N803
    limit: Annotated[int, Field(description="Maximum trend records to return.")] = 20,
    ctx: Context = None,
) -> str:
    bundle = await _fhir_payload_or_context_bundle(ctx, patientId, fhirPayload)
    return _json_response(analyze_observation_trends(bundle, limit=limit))


async def detect_patient_urgent_observations(
    patientId: Annotated[str | None, Field(description="Patient id. Optional when patient context exists.")] = None,  # noqa: N803
    fhirPayload: Annotated[dict[str, Any] | None, Field(description="Optional FHIR Bundle or resource payload.")] = None,  # noqa: N803
    ctx: Context = None,
) -> str:
    bundle = await _fhir_payload_or_context_bundle(ctx, patientId, fhirPayload)
    return _json_response(detect_urgent_observations(bundle))


async def draft_trend_followup_tasks(
    analysis: Annotated[dict[str, Any], Field(description="Lab/vitals trend analysis output.")],
) -> str:
    return _json_response(recommend_trend_followup(analysis))


async def check_prior_authorization_requirement(
    request: Annotated[dict[str, Any], Field(description="Requested medication, service, procedure, payer, and notes.")],
) -> str:
    return _json_response(check_requirement(request))


async def match_prior_authorization_evidence(
    requirement: Annotated[dict[str, Any], Field(description="Prior authorization requirement output.")],
    patientId: Annotated[str | None, Field(description="Patient id. Optional when patient context exists.")] = None,  # noqa: N803
    fhirPayload: Annotated[dict[str, Any] | None, Field(description="Optional FHIR Bundle or resource payload.")] = None,  # noqa: N803
    ctx: Context = None,
) -> str:
    bundle = await _fhir_payload_or_context_bundle(ctx, patientId, fhirPayload)
    return _json_response(match_evidence(requirement, bundle))


async def draft_prior_authorization_packet(
    request: Annotated[dict[str, Any], Field(description="Prior authorization request.")],
    requirement: Annotated[dict[str, Any], Field(description="Requirement output.")],
    evidence: Annotated[dict[str, Any], Field(description="Evidence matching output.")],
) -> str:
    return _json_response(draft_packet(request, requirement, evidence))


async def draft_prior_authorization_appeal(
    denial: Annotated[dict[str, Any], Field(description="Denial reasons and context.")],
    evidence: Annotated[dict[str, Any], Field(description="Evidence matching output.")],
) -> str:
    return _json_response(draft_appeal(denial, evidence))


async def suggest_clinical_code_candidates(
    patientId: Annotated[str | None, Field(description="Patient id. Optional when patient context exists.")] = None,  # noqa: N803
    note: Annotated[str | None, Field(description="Optional encounter note or documentation text.")] = None,
    fhirPayload: Annotated[dict[str, Any] | None, Field(description="Optional FHIR Bundle or resource payload.")] = None,  # noqa: N803
    ctx: Context = None,
) -> str:
    bundle = await _fhir_payload_or_context_bundle(ctx, patientId, fhirPayload)
    return _json_response(suggest_code_candidates({"fhir": bundle, "note": note or ""}))


async def identify_coding_documentation_gaps(
    patientId: Annotated[str | None, Field(description="Patient id. Optional when patient context exists.")] = None,  # noqa: N803
    fhirPayload: Annotated[dict[str, Any] | None, Field(description="Optional FHIR Bundle or resource payload.")] = None,  # noqa: N803
    ctx: Context = None,
) -> str:
    bundle = await _fhir_payload_or_context_bundle(ctx, patientId, fhirPayload)
    return _json_response(identify_documentation_gaps({"fhir": bundle}))


async def suppress_unsupported_clinical_codes(
    candidates: Annotated[list[dict[str, Any]], Field(description="Code candidates to filter.")],
) -> str:
    return _json_response(suppress_unsupported_codes(candidates))


async def build_transition_discharge_brief(
    patientId: Annotated[str | None, Field(description="Patient id. Optional when patient context exists.")] = None,  # noqa: N803
    fhirPayload: Annotated[dict[str, Any] | None, Field(description="Optional FHIR Bundle or resource payload.")] = None,  # noqa: N803
    ctx: Context = None,
) -> str:
    bundle = await _fhir_payload_or_context_bundle(ctx, patientId, fhirPayload)
    return _json_response(build_discharge_brief(bundle))


async def draft_transition_patient_instructions(
    dischargeBrief: Annotated[dict[str, Any], Field(description="Transition or discharge brief output.")],  # noqa: N803
    readingLevel: Annotated[str, Field(description="Target reading level.")] = "plain-language",  # noqa: N803
) -> str:
    return _json_response(draft_patient_instructions(dischargeBrief, reading_level=readingLevel))


async def create_transition_followup_tasks(
    patientId: Annotated[str | None, Field(description="Patient id. Optional when patient context exists.")] = None,  # noqa: N803
    fhirPayload: Annotated[dict[str, Any] | None, Field(description="Optional FHIR Bundle or resource payload.")] = None,  # noqa: N803
    ctx: Context = None,
) -> str:
    bundle = await _fhir_payload_or_context_bundle(ctx, patientId, fhirPayload)
    return _json_response(create_followup_tasks(bundle))


async def check_patient_referral_readiness(
    referral: Annotated[dict[str, Any], Field(description="Referral draft with specialty, reason, and routing context.")],
    patientId: Annotated[str | None, Field(description="Patient id. Optional when patient context exists.")] = None,  # noqa: N803
    fhirPayload: Annotated[dict[str, Any] | None, Field(description="Optional FHIR Bundle or resource payload.")] = None,  # noqa: N803
    ctx: Context = None,
) -> str:
    bundle = await _fhir_payload_or_context_bundle(ctx, patientId, fhirPayload)
    return _json_response(check_referral_readiness(referral, bundle))


async def evaluate_patient_referral_need(
    referral: Annotated[dict[str, Any], Field(description="Referral draft with specialty, reason, and routing context.")],
    patientId: Annotated[str | None, Field(description="Patient id. Optional when patient context exists.")] = None,  # noqa: N803
    fhirPayload: Annotated[dict[str, Any] | None, Field(description="Optional FHIR Bundle or resource payload.")] = None,  # noqa: N803
    ctx: Context = None,
) -> str:
    bundle = await _fhir_payload_or_context_bundle(ctx, patientId, fhirPayload)
    return _json_response(evaluate_referral_need(referral, bundle))


async def route_patient_referral(
    referral: Annotated[dict[str, Any], Field(description="Referral draft with specialty, reason, and routing context.")],
    routingPolicy: Annotated[dict[str, Any] | None, Field(description="Optional routing policy map.")] = None,  # noqa: N803
    patientId: Annotated[str | None, Field(description="Patient id. Optional when patient context exists.")] = None,  # noqa: N803
    fhirPayload: Annotated[dict[str, Any] | None, Field(description="Optional FHIR Bundle or resource payload.")] = None,  # noqa: N803
    ctx: Context = None,
) -> str:
    bundle = await _fhir_payload_or_context_bundle(ctx, patientId, fhirPayload)
    return _json_response(route_referral(referral, bundle, routing_policy=routingPolicy))


async def detect_patient_duplicate_referrals(
    referral: Annotated[dict[str, Any], Field(description="Referral draft with specialty, reason, and routing context.")],
    patientId: Annotated[str | None, Field(description="Patient id. Optional when patient context exists.")] = None,  # noqa: N803
    fhirPayload: Annotated[dict[str, Any] | None, Field(description="Optional FHIR Bundle or resource payload.")] = None,  # noqa: N803
    ctx: Context = None,
) -> str:
    bundle = await _fhir_payload_or_context_bundle(ctx, patientId, fhirPayload)
    return _json_response(detect_duplicate_referrals(referral, bundle))


async def validate_clinical_workflow_output(
    output: Annotated[dict[str, Any], Field(description="Shared clinical workflow output to validate.")],
) -> str:
    return _json_response(validate_workflow_output(output))


async def score_clinical_workflow_risk(
    findings: Annotated[list[dict[str, Any]] | None, Field(description="Workflow findings to score.")] = None,
    blockedActions: Annotated[list[str] | None, Field(description="Actions blocked by the agent.")] = None,  # noqa: N803
    urgent: Annotated[bool, Field(description="Whether urgent escalation is present.")] = False,
) -> str:
    return _json_response(score_workflow_risk(findings or [], blockedActions or [], urgent))


async def create_clinical_workflow_audit_event(
    output: Annotated[dict[str, Any], Field(description="Shared clinical workflow output.")],
    reviewerAction: Annotated[str, Field(description="Reviewer action.")] = "pending",  # noqa: N803
    overrideReason: Annotated[str, Field(description="Override reason, if any.")] = "",  # noqa: N803
) -> str:
    return _json_response(
        create_audit_event(
            output=output,
            reviewer_action=reviewerAction,
            override_reason=overrideReason,
        )
    )


async def _fhir_payload_or_context_bundle(
    ctx: Context,
    patient_id: str | None,
    fhir_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    if fhir_payload:
        return fhir_payload

    if not patient_id:
        patient_id = get_patient_id_if_context_exists(ctx)
    if not patient_id:
        raise ValueError("No patient context found")

    fhir_context = get_fhir_context(ctx)
    if not fhir_context:
        raise ValueError("The fhir context could not be retrieved")

    fhir_client = FhirClient(base_url=fhir_context.url, token=fhir_context.token)
    entries = []
    patient = await fhir_client.read(f"Patient/{patient_id}")
    if patient:
        entries.append({"resource": patient})

    for resource_type in FHIR_RESOURCE_TYPES:
        bundle = await fhir_client.search(resource_type, {"patient": patient_id})
        for entry in (bundle or {}).get("entry", []):
            resource = entry.get("resource") if isinstance(entry, dict) else None
            if resource:
                entries.append({"resource": resource})

    return {"resourceType": "Bundle", "entry": entries}


def _json_response(payload: dict[str, Any]) -> str:
    return create_text_response(json.dumps(payload, indent=2, sort_keys=True))
