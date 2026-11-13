import hmac
import os
from typing import Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from services.mobile_notifications import (
    acknowledge_alert,
    create_alert,
    list_alerts,
    mark_alert_push_sent,
    pending_push_alert_ids,
    save_subscription,
)
from services.web_push import public_key, send_alert_notification


router = APIRouter(prefix="/api/mobile", tags=["Mobile doctor app"])


class AlertPayload(BaseModel):
    patient_id: str = Field(min_length=1, max_length=80)
    patient_name: str = Field(min_length=1, max_length=120)
    severity: Literal["Urgent", "Review", "Watch", "Sensor issue"]
    message: str = Field(min_length=1, max_length=1000)
    recommended_action: str = Field(min_length=1, max_length=1000)
    rule_id: str = Field(min_length=1, max_length=120)
    reading_time: str = Field(min_length=1, max_length=100)


class PushSubscription(BaseModel):
    endpoint: str = Field(min_length=1, max_length=4000)
    keys: dict[str, str]


def _configured_secret(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise HTTPException(status_code=503, detail=f"{name} is not configured")
    return value


def _authorize_doctor(authorization: str | None) -> None:
    expected = _configured_secret("MINEARENA_DOCTOR_ACCESS_TOKEN")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Doctor sign-in required")
    supplied = authorization[7:]
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Invalid access code")


@router.post("/doctor/session")
def verify_doctor_access(authorization: str | None = Header(default=None)):
    _authorize_doctor(authorization)
    return {"authenticated": True}


@router.get("/doctor/alerts")
def get_doctor_alerts(authorization: str | None = Header(default=None)):
    _authorize_doctor(authorization)
    return {"alerts": list_alerts()}


@router.patch("/doctor/alerts/{alert_id}/acknowledge")
def acknowledge_doctor_alert(
    alert_id: int, authorization: str | None = Header(default=None)
):
    _authorize_doctor(authorization)
    if not acknowledge_alert(alert_id):
        raise HTTPException(status_code=404, detail="Alert not found or already acknowledged")
    return {"acknowledged": True}


@router.get("/doctor/push-key")
def get_push_key(authorization: str | None = Header(default=None)):
    _authorize_doctor(authorization)
    try:
        return {"public_key": public_key()}
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/doctor/push-subscriptions")
def register_push_subscription(
    subscription: PushSubscription,
    authorization: str | None = Header(default=None),
):
    _authorize_doctor(authorization)
    if not subscription.endpoint.startswith("https://"):
        raise HTTPException(status_code=422, detail="Push endpoint must use HTTPS")
    if not {"p256dh", "auth"}.issubset(subscription.keys):
        raise HTTPException(status_code=422, detail="Push subscription keys are incomplete")
    save_subscription(subscription.model_dump())
    try:
        for alert_id in pending_push_alert_ids():
            if send_alert_notification(alert_id):
                mark_alert_push_sent(alert_id)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {"subscribed": True}


@router.post("/alerts")
def ingest_monitor_alert(
    alert: AlertPayload,
    x_alert_ingest_token: str | None = Header(default=None),
):
    expected = _configured_secret("MINEARENA_ALERT_INGEST_TOKEN")
    if not x_alert_ingest_token or not hmac.compare_digest(
        x_alert_ingest_token, expected
    ):
        raise HTTPException(status_code=401, detail="Invalid alert-ingest token")

    alert_id, created, push_sent = create_alert(**alert.model_dump())
    if push_sent:
        return {
            "alert_id": alert_id,
            "created": created,
            "push_delivered": 0,
            "push_status": "already_sent",
        }

    try:
        delivered = send_alert_notification(alert_id)
    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=f"Alert was saved, but mobile push delivery failed: {error}",
        ) from error
    if delivered:
        mark_alert_push_sent(alert_id)
    return {
        "alert_id": alert_id,
        "created": created,
        "push_delivered": delivered,
        "push_status": "sent" if delivered else "no_subscribers",
    }
