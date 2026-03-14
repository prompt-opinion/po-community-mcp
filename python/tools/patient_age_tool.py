from datetime import date

from mcp.server.fastmcp import FastMCP

from fhir_client import fhir_client_instance
from fhir_utilities import get_patient_id_if_context_exists
from i_mcp_tool import IMcpTool
from mcp_utilities import create_text_response
from request_context import get_request


class PatientAgeTool(IMcpTool):
    def register_tool(self, mcp: FastMCP) -> None:
        @mcp.tool(description="Gets the age of a patient.")
        async def get_patient_age(patient_id: str | None = None) -> str:
            req = get_request()

            if not patient_id:
                patient_id = get_patient_id_if_context_exists(req)
                if not patient_id:
                    raise ValueError("No patient context found")

            patient = await fhir_client_instance.read(req, f"Patient/{patient_id}")
            if not patient:
                return create_text_response("The patient could not be found.", is_error=True)

            birth_date_str = patient.get("birthDate")
            if not birth_date_str:
                return create_text_response("A birth date could not be found for the patient.", is_error=True)

            try:
                birth_date = date.fromisoformat(birth_date_str)
                today = date.today()
                age = today.year - birth_date.year - (
                    (today.month, today.day) < (birth_date.month, birth_date.day)
                )
                return create_text_response(f"The patient's age is: {age}")
            except ValueError:
                return create_text_response("Could not parse the patient's birth date.", is_error=True)


patient_age_tool_instance = PatientAgeTool()
