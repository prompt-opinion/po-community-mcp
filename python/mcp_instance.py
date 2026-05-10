from mcp.server.fastmcp import FastMCP
from tools.clinical_workflow_tools import (
    analyze_patient_lab_vitals_trends,
    build_transition_discharge_brief,
    call_owned_clinical_workflow_tool,
    check_patient_referral_readiness,
    check_prior_authorization_requirement,
    create_clinical_workflow_audit_event,
    create_transition_followup_tasks,
    detect_patient_duplicate_referrals,
    detect_patient_urgent_observations,
    draft_patient_care_gap_tasks,
    draft_prior_authorization_appeal,
    draft_prior_authorization_packet,
    draft_transition_patient_instructions,
    draft_trend_followup_tasks,
    evaluate_patient_care_gaps,
    evaluate_patient_referral_need,
    get_clinical_chart_summary,
    get_clinical_patient_snapshot,
    identify_coding_documentation_gaps,
    list_owned_clinical_workflow_tools,
    match_prior_authorization_evidence,
    prioritize_patient_care_gaps,
    review_clinical_medications,
    route_patient_referral,
    score_clinical_workflow_risk,
    suggest_clinical_code_candidates,
    suggest_medication_review_actions,
    suppress_unsupported_clinical_codes,
    validate_clinical_workflow_output,
)
from tools.patient_age_tool import get_patient_age
from tools.patient_allergies_tool import get_patient_allergies
from tools.patient_id_tool import find_patient_id

mcp = FastMCP("Python Template", stateless_http=True, host="0.0.0.0")

_original_get_capabilities = mcp._mcp_server.get_capabilities

def _patched_get_capabilities(notification_options, experimental_capabilities):
    caps = _original_get_capabilities(notification_options, experimental_capabilities)
    caps.model_extra["extensions"] = {
        "ai.promptopinion/fhir-context": {
            "scopes": [
                {"name": "patient/Patient.rs", "required": True},
                {"name": "patient/Observation.rs"},
                {"name": "patient/MedicationStatement.rs"},
                {"name": "patient/MedicationRequest.rs"},
                {"name": "patient/MedicationDispense.rs"},
                {"name": "patient/Condition.rs"},
                {"name": "patient/AllergyIntolerance.rs"},
                {"name": "patient/Encounter.rs"},
                {"name": "patient/ServiceRequest.rs"},
                {"name": "patient/Coverage.rs"},
                {"name": "patient/Claim.rs"},
                {"name": "patient/ExplanationOfBenefit.rs"},
                {"name": "patient/Immunization.rs"},
                {"name": "patient/Procedure.rs"},
                {"name": "patient/DocumentReference.rs"},
            ]
        }
    }
    return caps

mcp._mcp_server.get_capabilities = _patched_get_capabilities



mcp.tool(name="GetPatientAge", description="Gets the age of a patient.")(get_patient_age)
mcp.tool(name="GetPatientAllergies", description="Gets the known allergies of a patient.")(get_patient_allergies)
mcp.tool(name="FindPatientId", description="Finds a patient id given a first name and last name")(find_patient_id)

mcp.tool(name="ListOwnedClinicalWorkflowTools", description="Lists all owned clinical workflow tools available in this server.")(list_owned_clinical_workflow_tools)
mcp.tool(name="CallOwnedClinicalWorkflowTool", description="Calls an owned clinical workflow tool by name with a JSON payload.")(call_owned_clinical_workflow_tool)
mcp.tool(name="GetClinicalPatientSnapshot", description="Normalizes patient FHIR context into a clinical workflow snapshot.")(get_clinical_patient_snapshot)
mcp.tool(name="GetClinicalChartSummary", description="Builds an evidence-linked clinical chart summary for human review.")(get_clinical_chart_summary)
mcp.tool(name="ReviewClinicalMedications", description="Reviews medications for duplicate, allergy, interaction, and renal-risk signals.")(review_clinical_medications)
mcp.tool(name="SuggestMedicationReviewActions", description="Drafts medication review actions from detected medication safety issues.")(suggest_medication_review_actions)
mcp.tool(name="EvaluatePatientCareGaps", description="Evaluates preventive, chronic-care, and documentation care gaps.")(evaluate_patient_care_gaps)
mcp.tool(name="PrioritizePatientCareGaps", description="Prioritizes evaluated care gaps by risk and certainty.")(prioritize_patient_care_gaps)
mcp.tool(name="DraftPatientCareGapTasks", description="Drafts care-gap review tasks without direct outreach or order placement.")(draft_patient_care_gap_tasks)
mcp.tool(name="AnalyzePatientLabVitalsTrends", description="Analyzes Observation trends for labs and vitals.")(analyze_patient_lab_vitals_trends)
mcp.tool(name="DetectPatientUrgentObservations", description="Detects urgent lab or vital threshold crossings.")(detect_patient_urgent_observations)
mcp.tool(name="DraftTrendFollowupTasks", description="Drafts follow-up tasks from trend analysis.")(draft_trend_followup_tasks)
mcp.tool(name="CheckPriorAuthorizationRequirement", description="Checks whether a request likely requires prior authorization.")(check_prior_authorization_requirement)
mcp.tool(name="MatchPriorAuthorizationEvidence", description="Matches patient evidence to prior authorization criteria.")(match_prior_authorization_evidence)
mcp.tool(name="DraftPriorAuthorizationPacket", description="Drafts a prior authorization packet for human review.")(draft_prior_authorization_packet)
mcp.tool(name="DraftPriorAuthorizationAppeal", description="Drafts a prior authorization appeal outline for human review.")(draft_prior_authorization_appeal)
mcp.tool(name="SuggestClinicalCodeCandidates", description="Suggests evidence-backed clinical code candidates with coder review guardrails.")(suggest_clinical_code_candidates)
mcp.tool(name="IdentifyCodingDocumentationGaps", description="Identifies documentation gaps that prevent confident coding.")(identify_coding_documentation_gaps)
mcp.tool(name="SuppressUnsupportedClinicalCodes", description="Suppresses code candidates with low confidence or missing evidence.")(suppress_unsupported_clinical_codes)
mcp.tool(name="BuildTransitionDischargeBrief", description="Builds a transition-ready discharge or handoff brief.")(build_transition_discharge_brief)
mcp.tool(name="DraftTransitionPatientInstructions", description="Drafts patient instructions from a transition brief for clinician review.")(draft_transition_patient_instructions)
mcp.tool(name="CreateTransitionFollowupTasks", description="Creates draft transition follow-up tasks.")(create_transition_followup_tasks)
mcp.tool(name="CheckPatientReferralReadiness", description="Checks whether a referral packet has minimum supporting context.")(check_patient_referral_readiness)
mcp.tool(name="EvaluatePatientReferralNeed", description="Evaluates referral readiness, red flags, duplicates, and likely specialty.")(evaluate_patient_referral_need)
mcp.tool(name="RoutePatientReferral", description="Drafts referral routing queue and network selection without dispatching.")(route_patient_referral)
mcp.tool(name="DetectPatientDuplicateReferrals", description="Detects likely duplicate referral ServiceRequest records.")(detect_patient_duplicate_referrals)
mcp.tool(name="ValidateClinicalWorkflowOutput", description="Validates the shared clinical workflow output contract.")(validate_clinical_workflow_output)
mcp.tool(name="ScoreClinicalWorkflowRisk", description="Scores clinical workflow risk from findings and blocked actions.")(score_clinical_workflow_risk)
mcp.tool(name="CreateClinicalWorkflowAuditEvent", description="Creates a PHI-minimized audit event for a clinical workflow output.")(create_clinical_workflow_audit_event)
