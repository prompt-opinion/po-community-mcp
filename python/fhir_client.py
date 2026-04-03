import httpx
from mcp.server.fastmcp import Context

from fhir_context import FhirContext
from fhir_utilities import get_fhir_context


class FhirClient:
    def _get_fhir_context_or_throw(self, ctx: Context) -> FhirContext:
        context = get_fhir_context(ctx)
        if not context:
            raise ValueError("The fhir context could not be retrieved")
        return context

    def _build_url(self, context: FhirContext, path: str) -> str:
        if path.startswith("/"):
            path = path[1:]
        return f"{context.url}/{path}"

    async def _get(self, ctx: Context, path: str) -> dict | None:
        context = self._get_fhir_context_or_throw(ctx)
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

    async def read(self, ctx: Context, path: str) -> dict | None:
        return await self._get(ctx, path)

    async def search(self, ctx: Context, resource_type: str, search_parameters: list[str]) -> dict | None:
        query = "&".join(search_parameters)
        return await self._get(ctx, f"{resource_type}?{query}")


fhir_client_instance = FhirClient()
