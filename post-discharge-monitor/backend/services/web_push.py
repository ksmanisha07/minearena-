import base64
import json
import os

from pywebpush import WebPushException, webpush

from services.mobile_notifications import list_subscriptions, remove_subscription


def public_key() -> str:
    value = os.environ.get("MINEARENA_VAPID_PUBLIC_KEY", "").strip()
    if not value:
        raise RuntimeError("MINEARENA_VAPID_PUBLIC_KEY is not configured")
    return value


def send_alert_notification(alert_id: int) -> int:
    encoded_private_key = os.environ.get("MINEARENA_VAPID_PRIVATE_KEY_B64", "").strip()
    if not encoded_private_key:
        raise RuntimeError("MINEARENA_VAPID_PRIVATE_KEY_B64 is not configured")
    try:
        padding = "=" * ((4 - len(encoded_private_key) % 4) % 4)
        base64.b64decode(encoded_private_key + padding, altchars=b"-_", validate=True)
    except ValueError as error:
        raise RuntimeError("MINEARENA_VAPID_PRIVATE_KEY_B64 is invalid") from error

    subject = os.environ.get("MINEARENA_VAPID_SUBJECT", "").strip()
    if not subject.startswith(("mailto:", "https://")):
        raise RuntimeError("MINEARENA_VAPID_SUBJECT must be a mailto: or https:// URL")

    subscriptions = list_subscriptions()
    delivered = 0
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info=subscription,
                data=json.dumps({"type": "new-alert", "alertId": alert_id}),
                vapid_private_key=encoded_private_key,
                vapid_claims={"sub": subject},
            )
            delivered += 1
        except WebPushException as error:
            response = getattr(error, "response", None)
            status_code = getattr(response, "status_code", None)
            if status_code in (404, 410):
                remove_subscription(str(subscription["endpoint"]))
                continue
            raise RuntimeError(f"Web Push delivery failed: {error}") from error
    return delivered
