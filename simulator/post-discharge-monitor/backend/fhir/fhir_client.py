import httpx
import os

FHIR_BASE_URL = os.getenv("FHIR_BASE_URL", "http://localhost:8080/fhir")

async def create_fhir_resource(resource: dict):
    resource_type = resource.get("resourceType")

    if not resource_type:
        raise ValueError("Missing resourceType")

    url = f"{FHIR_BASE_URL}/{resource_type}"

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            url,
            json=resource,
            headers={"Content-Type": "application/fhir+json"}
        )

    response.raise_for_status()
    return response.json()

async def get_fhir_resource(resource_type: str, resource_id: str):
    url = f"{FHIR_BASE_URL}/{resource_type}/{resource_id}"

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url)

    response.raise_for_status()
    return response.json()

async def search_fhir_resources(resource_type: str, params: dict = None):
    url = f"{FHIR_BASE_URL}/{resource_type}"

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, params=params or {})

    response.raise_for_status()
    return response.json()