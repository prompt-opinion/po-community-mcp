from mcp.server.fastmcp import FastMCP
from fastapi import Request

from fhir_client import fhir_client_instance
from i_mcp_tool import IMcpTool
from mcp_utilities import create_text_response
from request_context import get_request


class PatientIdTool(IMcpTool):
    def register_tool(self, mcp: FastMCP) -> None:
        @mcp.tool(description="Finds a patient id given a first name and last name.")
        async def find_patient_id(first_name: str, last_name: str | None = None) -> str:
            req = get_request()

            patients = await self._patient_searcher(req, first_name, last_name)
            if not patients:
                patients = await self._patient_searcher(req, last_name, first_name)

            if patients and len(patients) > 1:
                return create_text_response("More than one patient was found. Provide more details.", is_error=True)

            if patients and patients[0].get("id"):
                return create_text_response(patients[0]["id"])

            return create_text_response("No patient could be found with that name", is_error=True)

    async def _patient_searcher(
        self,
        req: Request,
        search_first_name: str | None,
        search_last_name: str | None,
    ) -> list[dict] | None:
        search_parameters: list[str] = []
        if search_first_name:
            search_parameters.append(f"given={search_first_name}")
        if search_last_name:
            search_parameters.append(f"family={search_last_name}")

        bundle = await fhir_client_instance.search(req, "Patient", search_parameters)
        if not bundle or not bundle.get("entry"):
            return None

        return [
            entry["resource"]
            for entry in bundle["entry"]
            if entry.get("resource")
        ]


patient_id_tool_instance = PatientIdTool()
