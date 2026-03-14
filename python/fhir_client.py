import httpx
from fastapi import Request

from fhir_context import FhirContext
from fhir_utilities import get_fhir_context


class FhirClient:
    def _get_fhir_context_or_throw(self, req: Request) -> FhirContext:
        context = get_fhir_context(req)
        if not context:
            raise ValueError("The fhir context could not be retrieved")
        return context

    def _build_url(self, context: FhirContext, path: str) -> str:
        if path.startswith("/"):
            path = path[1:]
        return f"{context.url}/{path}"

    async def _get(self, req: Request, path: str) -> dict | None:
        context = self._get_fhir_context_or_throw(req)
        headers = {}
        if context.token:
            headers["Authorization"] = f"Bearer {context.token}"
        url = self._build_url(context, path)
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError:
                raise

    async def read(self, req: Request, path: str) -> dict | None:
        return await self._get(req, path)

    async def search(self, req: Request, resource_type: str, search_parameters: list[str]) -> dict | None:
        query = "&".join(search_parameters)
        return await self._get(req, f"{resource_type}?{query}")


fhir_client_instance = FhirClient()
