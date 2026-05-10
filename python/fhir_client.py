import httpx


class FhirClient:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _build_url(self, path: str) -> str:
        path = path.lstrip("/")
        return f"{self.base_url}/{path}"

    async def _get(self, path: str, params: dict[str, str] | None = None) -> dict | None:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        url = self._build_url(path)
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError:
                raise

    async def _post(self, path: str, body: dict) -> dict:
        headers = {
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        url = self._build_url(path)
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            # Most FHIR servers return the created resource as JSON; some return
            # just a Location header with an empty body — tolerate both.
            try:
                return response.json()
            except ValueError:
                return {"_status_code": response.status_code, "_location": response.headers.get("Location")}

    async def read(self, path: str) -> dict | None:
        return await self._get(path)

    async def search(
        self,
        resource_type: str,
        search_parameters: dict[str, str] | None = None,
    ) -> dict | None:
        return await self._get(resource_type, params=search_parameters)

    async def create(self, resource_type: str, body: dict) -> dict:
        """POST a new resource. Server typically returns the persisted resource
        with a server-assigned `id`."""
        return await self._post(resource_type, body)
