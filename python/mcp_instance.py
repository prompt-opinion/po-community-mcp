from mcp.server.fastmcp import FastMCP
from tools.dispatch_postpartum_alert_tool import dispatch_postpartum_alert
from tools.find_clinical_trials_tool import find_clinical_trials_for_patient
from tools.patient_age_tool import get_patient_age
from tools.patient_allergies_tool import get_patient_allergies
from tools.patient_id_tool import find_patient_id
from tools.postpartum_policy_tool import analyze_postpartum_coverage

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
                {"name": "patient/Condition.rs"},
                {"name": "patient/DocumentReference.rs"},
                {"name": "patient/Coverage.rs"},
                {"name": "patient/Encounter.rs"},
                # Write scope: lets DispatchPostpartumAlert log a
                # CommunicationRequest back to the chart after sending the SMS.
                {"name": "patient/CommunicationRequest.c"},
            ]
        }
    }
    return caps

mcp._mcp_server.get_capabilities = _patched_get_capabilities



mcp.tool(name="GetPatientAge", description="Gets the age of a patient.")(get_patient_age)
mcp.tool(name="GetPatientAllergies", description="Gets the known allergies of a patient.")(get_patient_allergies)
mcp.tool(name="FindPatientId", description="Finds a patient id given a first name and last name")(find_patient_id)

mcp.tool(
    name="AnalyzePostpartumCoverage",
    description=(
        "Trajectory.OS: Calculates the postpartum Medicaid coverage cliff for a patient. "
        "Determines the exact date their Medicaid expires (60 days post-delivery) and the "
        "days remaining. If the cliff is within 15 days (CRITICAL), autonomously generates "
        "a Zero-Click intervention payload containing: a pre-drafted patient SMS alert, a "
        "fully pre-filled state-specific Medicaid extension form (ARPA 12-month where "
        "available), and a 6-week OB/GYN appointment flag with required screenings. "
        "Use this tool when reviewing a postpartum patient chart for coverage or "
        "administrative risks. After this returns CRITICAL or EXPIRED, call "
        "DispatchPostpartumAlert to actually send the SMS. If the patient was "
        "denied a medication or needs a coverage alternative, call "
        "FindClinicalTrialsForPatient as a Plan B."
    ),
)(analyze_postpartum_coverage)

mcp.tool(
    name="DispatchPostpartumAlert",
    description=(
        "Trajectory.OS Zero-Click execution: actually dispatches the drafted SMS alert "
        "to the patient via Twilio AND logs a FHIR CommunicationRequest back to the "
        "patient's chart for permanent audit trail. Call this AFTER AnalyzePostpartumCoverage "
        "returns status=CRITICAL or status=EXPIRED. The tool re-runs the analysis (so the "
        "message reflects current data), sends the SMS to the patient's mobile number on "
        "file (or to TWILIO_DEMO_RECIPIENT_OVERRIDE in demo mode), then writes the "
        "intervention back to the EHR as a FHIR CommunicationRequest resource. Returns a "
        "dispatch confirmation including Twilio message SID, delivery status, the sent body, "
        "and the chart write-back audit trail."
    ),
)(dispatch_postpartum_alert)

mcp.tool(
    name="FindClinicalTrialsForPatient",
    description=(
        "Trajectory.OS 'Plan B': queries ClinicalTrials.gov for actively recruiting "
        "clinical trials matching a condition or medication, filtered by the patient's "
        "state when patient context is available. Use this when standard care fails — "
        "prior-auth denial, expiring coverage, or the patient cannot afford a medication. "
        "Trials typically provide study medication and care at no cost. Returns the top "
        "matches (NCT ID, title, sponsor, recruiting locations, ClinicalTrials.gov URL) "
        "and a drafted referral letter the clinician can send to the patient."
    ),
)(find_clinical_trials_for_patient)
