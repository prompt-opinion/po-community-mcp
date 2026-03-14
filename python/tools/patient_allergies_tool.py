from mcp.server.fastmcp import FastMCP

from fhir_client import fhir_client_instance
from fhir_utilities import get_patient_id_if_context_exists
from i_mcp_tool import IMcpTool
from mcp_utilities import create_text_response
from request_context import get_request


class PatientAllergiesTool(IMcpTool):
    def register_tool(self, mcp: FastMCP) -> None:
        @mcp.tool(description="Gets the known allergies of a patient.")
        async def get_patient_allergies(patient_id: str | None = None) -> str:
            req = get_request()

            if not patient_id:
                patient_id = get_patient_id_if_context_exists(req)
                if not patient_id:
                    raise ValueError("No patient context found")

            bundle = await fhir_client_instance.search(req, "AllergyIntolerance", [f"patient={patient_id}"])

            if not bundle or not bundle.get("entry"):
                return create_text_response("No known allergies found for this patient.")

            allergies = []
            for entry in bundle["entry"]:
                resource = entry.get("resource", {})
                code = resource.get("code", {})
                name = code.get("text") or (code.get("coding") or [{}])[0].get("display")
                if name:
                    allergies.append(name)

            if not allergies:
                return create_text_response("No known allergies found for this patient.")

            return create_text_response(f"Known allergies: {', '.join(allergies)}.")


patient_allergies_tool_instance = PatientAllergiesTool()
