from fastapi import APIRouter, HTTPException
from fhir.fhir_client import search_fhir_resources

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("/{patient_id}/observations")
async def get_patient_observations(patient_id: str):
    try:
        response = await search_fhir_resources(
            "Observation",
            {
                "patient": f"Patient/{patient_id}",
                "_sort": "-date",
                "_count": "100"
            }
        )
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"FHIR server error: {str(error)}"
        )

    return {
        "patient_id": patient_id,
        "total": response.get("total", 0),
        "observations": response.get("entry", [])
    }