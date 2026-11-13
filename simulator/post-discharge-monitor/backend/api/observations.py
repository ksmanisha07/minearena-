from fastapi import APIRouter, HTTPException
from fhir.fhir_client import create_fhir_resource
from fhir.validators import validate_observation

router = APIRouter(prefix="/fhir", tags=["FHIR Observations"])

@router.post("/Observation")
async def create_observation(observation: dict):
    errors = validate_observation(observation)

    if errors:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid FHIR Observation",
                "errors": errors
            }
        )

    try:
        saved_resource = await create_fhir_resource(observation)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Could not store observation in HAPI FHIR",
                "error": str(error)
            }
        )

    return {
        "status": "stored",
        "resource_id": saved_resource.get("id"),
        "resource_type": saved_resource.get("resourceType"),
        "patient": observation.get("subject", {}).get("reference"),
        "loinc_code": observation["code"]["coding"][0]["code"],
        "value": observation["valueQuantity"]["value"],
        "unit": observation["valueQuantity"]["unit"],
        "timestamp": observation.get("effectiveDateTime")
    }