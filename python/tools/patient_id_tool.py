from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from fhir_client import fhir_client_instance
from mcp_utilities import create_text_response


async def find_patient_id(
    firstName: Annotated[str, Field(description="The patient's first name")],  # noqa: N803
    lastName: Annotated[str | None, Field(description="The patient's last name. This is optional")] = None,  # noqa: N803
    ctx: Context = None,
) -> str:
    patients = await _patient_searcher(ctx, firstName, lastName)
    if not patients:
        patients = await _patient_searcher(ctx, lastName, firstName)

    if patients and len(patients) > 1:
        return create_text_response("More than one patient was found. Provide more details.", is_error=True)

    if patients and patients[0].get("id"):
        return create_text_response(patients[0]["id"])

    return create_text_response("No patient could be found with that name", is_error=True)


async def _find_patient(
    ctx: Context,
    search_first_name: str | None,
    search_last_name: str | None,
) -> list[dict] | None:
    search_parameters: list[str] = []
    if search_first_name:
        search_parameters.append(f"given={search_first_name}")
    if search_last_name:
        search_parameters.append(f"family={search_last_name}")

    bundle = await fhir_client_instance.search(ctx, "Patient", search_parameters)
    if not bundle or not bundle.get("entry"):
        return None

    return [
        entry["resource"]
        for entry in bundle["entry"]
        if entry.get("resource")
    ]
