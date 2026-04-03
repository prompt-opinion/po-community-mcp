from mcp.server.fastmcp import Context

from fhir_client import fhir_client_instance
from fhir_utilities import get_patient_id_if_context_exists
from mcp_utilities import create_text_response


async def get_patient_allergies(patientId: str | None = None, ctx: Context = None) -> str:  # noqa: N803
    if not patientId:
        patientId = get_patient_id_if_context_exists(ctx)
        if not patientId:
            raise ValueError("No patient context found")

    bundle = await fhir_client_instance.search(ctx, "AllergyIntolerance", [f"patient={patientId}"])

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
