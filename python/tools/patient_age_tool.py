from datetime import date
from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from fhir_client import fhir_client_instance
from fhir_utilities import get_patient_id_if_context_exists
from mcp_utilities import create_text_response


async def get_patient_age(
    patientId: Annotated[  # noqa: N803
        str | None,
        Field(description="The id of the patient. This is optional if patient context already exists"),
    ] = None,
    ctx: Context = None,
) -> str:
    if not patientId:
        patientId = get_patient_id_if_context_exists(ctx)
        if not patientId:
            raise ValueError("No patient context found")

    patient = await fhir_client_instance.read(ctx, f"Patient/{patientId}")
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
