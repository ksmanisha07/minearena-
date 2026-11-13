from fastapi import APIRouter
from services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])
alert_service = AlertService()

@router.get("/{patient_id}")
async def get_alerts(patient_id: str):
    return alert_service.get_alerts(patient_id)

@router.post("/{patient_id}")
async def create_alert(patient_id: str, alert: dict):
    return alert_service.create_alert(patient_id, alert)