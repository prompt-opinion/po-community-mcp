from mcp.server.fastmcp import FastMCP
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
        "Use this tool when reviewing any postpartum patient chart for coverage or "
        "administrative risks."
    ),
)(analyze_postpartum_coverage)
