"""Owned composite MCP contracts and marketplace candidate ranking."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .registry import MarketplaceResource


@dataclass(frozen=True)
class CompositeTool:
    """A tool that an owned composite MCP should expose."""

    name: str
    description: str


@dataclass(frozen=True)
class CompositeSpec:
    """Contract and benchmark categories for an owned MCP."""

    slug: str
    name: str
    purpose: str
    primary_categories: tuple[str, ...]
    supporting_categories: tuple[str, ...]
    tools: tuple[CompositeTool, ...]

    @property
    def categories(self) -> tuple[str, ...]:
        ordered = list(self.primary_categories)
        for category in self.supporting_categories:
            if category not in ordered:
                ordered.append(category)
        return tuple(ordered)

    def to_dict(self) -> dict:
        return asdict(self)


COMPOSITE_SPECS: tuple[CompositeSpec, ...] = (
    CompositeSpec(
        slug="marketplace-quality-mcp",
        name="Marketplace Quality MCP",
        purpose="Validate marketplace listings, A2A cards, replacement readiness, and candidate rankings.",
        primary_categories=("marketplace-quality",),
        supporting_categories=(),
        tools=(
            CompositeTool("validate_listing", "Validate one marketplace MCP record."),
            CompositeTool("validate_marketplace_export", "Validate every listing in an exported marketplace payload."),
            CompositeTool("validate_a2a_card", "Validate one live A2A agent card payload."),
            CompositeTool("test_endpoint", "Probe one MCP endpoint without sending PHI."),
            CompositeTool("summarize_marketplace", "Summarize marketplace capability coverage."),
            CompositeTool("recommend_composite_mcps", "Rank existing MCPs as benchmarks for owned composites."),
            CompositeTool("build_replacement_plan", "Explain which marketplace records can or cannot be replaced."),
            CompositeTool("generate_parity_report", "Generate a benchmark report for owned MCP replacement."),
            CompositeTool("map_owned_tool_coverage", "Map owned tool contracts to marketplace benchmark tools."),
        ),
    ),
    CompositeSpec(
        slug="clinical-workflow-foundation-mcp",
        name="Clinical Workflow Foundation MCP",
        purpose="Provide common clinical output contracts, risk scoring, and audit events for all workflow agents.",
        primary_categories=("marketplace-quality", "chart-summary"),
        supporting_categories=("clinical-coding", "prior-auth", "referral"),
        tools=(
            CompositeTool("compose_workflow_output", "Compose the shared clinical workflow output contract."),
            CompositeTool("validate_workflow_output", "Validate the shared clinical workflow output contract."),
            CompositeTool("score_workflow_risk", "Score workflow risk from findings and blocked actions."),
            CompositeTool("create_audit_event", "Create a PHI-minimized audit event for a workflow output."),
        ),
    ),
    CompositeSpec(
        slug="clinical-foundation-mcp",
        name="Clinical Foundation MCP",
        purpose="Provide normalized patient context used by most clinical workflows.",
        primary_categories=("chart-summary", "lab-vitals-trend"),
        supporting_categories=("medication-review", "care-gap"),
        tools=(
            CompositeTool("get_patient_snapshot", "Return demographics, problems, meds, allergies, encounters, and recent observations."),
            CompositeTool("get_chart_summary", "Return a clinician-ready chart summary with source categories."),
            CompositeTool("get_recent_signals", "Return recent vitals, labs, notes, and clinical changes."),
        ),
    ),
    CompositeSpec(
        slug="medication-safety-mcp",
        name="Medication Safety MCP",
        purpose="Unify medication, allergy, interaction, contraindication, and dose review workflows.",
        primary_categories=("medication-review",),
        supporting_categories=("lab-vitals-trend", "clinical-coding"),
        tools=(
            CompositeTool("review_medications", "Review active medications for duplicate therapy, safety concerns, and missing context."),
            CompositeTool("check_interactions", "Check drug-drug, drug-allergy, and drug-condition interactions."),
            CompositeTool("suggest_safer_alternatives", "Suggest safer alternatives with evidence requirements and clinician-review flags."),
        ),
    ),
    CompositeSpec(
        slug="care-gap-mcp",
        name="Care Gap MCP",
        purpose="Evaluate preventive, chronic-care, documentation, and outreach gap workflows.",
        primary_categories=("care-gap",),
        supporting_categories=("chart-summary", "patient-education"),
        tools=(
            CompositeTool("evaluate_care_gaps", "Evaluate preventive and chronic-care gaps with configurable policy rules."),
            CompositeTool("prioritize_care_gaps", "Prioritize evaluated care gaps by risk and certainty."),
            CompositeTool("draft_care_gap_tasks", "Draft care-gap review tasks without direct outreach or orders."),
        ),
    ),
    CompositeSpec(
        slug="lab-vitals-trend-mcp",
        name="Lab/Vitals Trend MCP",
        purpose="Analyze Observation trends, urgent thresholds, and follow-up task drafts.",
        primary_categories=("lab-vitals-trend",),
        supporting_categories=("chart-summary", "care-gap"),
        tools=(
            CompositeTool("analyze_observation_trends", "Analyze lab and vital Observation trends."),
            CompositeTool("detect_urgent_observations", "Detect observations crossing urgent thresholds."),
            CompositeTool("recommend_trend_followup", "Draft follow-up tasks from trend analysis."),
        ),
    ),
    CompositeSpec(
        slug="prior-auth-workflow-mcp",
        name="Prior Auth Workflow MCP",
        purpose="Combine payer policy, clinical evidence, packet drafting, and appeal support.",
        primary_categories=("prior-auth",),
        supporting_categories=("chart-summary", "clinical-coding", "medication-review"),
        tools=(
            CompositeTool("check_requirement", "Check whether a service or medication requires prior authorization."),
            CompositeTool("match_evidence", "Map patient evidence to payer criteria."),
            CompositeTool("draft_packet", "Draft a prior authorization packet for human review."),
            CompositeTool("draft_appeal", "Draft an appeal when criteria or denial context is available."),
        ),
    ),
    CompositeSpec(
        slug="clinical-coding-mcp",
        name="Clinical Coding MCP",
        purpose="Suggest evidence-backed coding candidates while preserving coder review and licensing guardrails.",
        primary_categories=("clinical-coding",),
        supporting_categories=("chart-summary", "scribe-documentation"),
        tools=(
            CompositeTool("suggest_code_candidates", "Suggest evidence-backed ICD candidates and procedure review candidates."),
            CompositeTool("identify_documentation_gaps", "Identify documentation gaps that prevent confident coding."),
            CompositeTool("suppress_unsupported_codes", "Suppress code candidates with low confidence or missing evidence."),
        ),
    ),
    CompositeSpec(
        slug="referral-routing-mcp",
        name="Referral Routing MCP",
        purpose="Evaluate referral readiness, duplicate risk, specialty routing, and network queue drafts.",
        primary_categories=("referral",),
        supporting_categories=("chart-summary", "care-gap"),
        tools=(
            CompositeTool("evaluate_referral_need", "Evaluate referral need, readiness, red flags, and likely specialty."),
            CompositeTool("route_referral", "Draft referral routing queue and network selection."),
            CompositeTool("detect_duplicate_referrals", "Detect likely duplicate referral ServiceRequest records."),
        ),
    ),
    CompositeSpec(
        slug="transition-of-care-mcp",
        name="Transition of Care MCP",
        purpose="Support discharge, referral, patient education, follow-up, and loop closure.",
        primary_categories=("referral", "patient-education", "care-gap"),
        supporting_categories=("medication-review", "chart-summary"),
        tools=(
            CompositeTool("build_discharge_brief", "Build a transition-ready clinical handoff."),
            CompositeTool("draft_patient_instructions", "Draft patient instructions at an appropriate reading level."),
            CompositeTool("create_followup_tasks", "Create follow-up tasks, labs, visits, and escalation checkpoints."),
            CompositeTool("check_referral_readiness", "Check whether referral packet evidence is complete."),
        ),
    ),
)


def composite_specs() -> tuple[CompositeSpec, ...]:
    """Return owned composite MCP specs in build order."""

    return COMPOSITE_SPECS


def rank_candidates(
    resources: list[MarketplaceResource],
    spec: CompositeSpec,
    limit: int | None = None,
) -> list[MarketplaceResource]:
    """Rank marketplace resources that can benchmark an owned composite MCP."""

    candidates = [
        resource
        for resource in resources
        if any(category in resource.categories for category in spec.primary_categories)
    ]

    def score(resource: MarketplaceResource) -> tuple[int, int, bool, bool, str]:
        primary_matches = sum(1 for category in spec.primary_categories if category in resource.categories)
        category_matches = sum(1 for category in spec.categories if category in resource.categories)
        tool_count = len(resource.tools)
        return (
            -primary_matches,
            -category_matches,
            -tool_count,
            not resource.supports_fhir_context,
            resource.auth_required,
            resource.name.lower(),
        )

    ranked = sorted(candidates, key=score)
    if limit is None:
        return ranked
    return ranked[:limit]


def candidate_to_dict(resource: MarketplaceResource, spec: CompositeSpec) -> dict:
    """Serialize a ranked candidate with match metadata."""

    return {
        "id": resource.id,
        "name": resource.name,
        "endpoint": resource.endpoint,
        "publisher": resource.publisher_name,
        "authRequired": resource.auth_required,
        "supportsFhirContext": resource.supports_fhir_context,
        "toolCount": len(resource.tools),
        "tools": list(resource.tools),
        "matchedCategories": [category for category in spec.categories if category in resource.categories],
    }
