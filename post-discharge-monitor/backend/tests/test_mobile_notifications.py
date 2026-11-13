import base64
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from services.mobile_notifications import (
    acknowledge_alert,
    create_alert,
    list_alerts,
    list_subscriptions,
    mark_alert_push_sent,
    pending_push_alert_ids,
    save_subscription,
)
from services.web_push import send_alert_notification


class MobileNotificationStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.environment = patch.dict(
            os.environ,
            {"MINEARENA_MOBILE_DB": os.path.join(self.temp_dir.name, "mobile.sqlite3")},
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.addCleanup(self.temp_dir.cleanup)

    def create_alert(self, reading_time="2026-11-13T00:00:00"):
        return create_alert(
            patient_id="P-001",
            patient_name="Ramesh",
            severity="Urgent",
            message="Urgent review needed",
            recommended_action="Immediate clinical review",
            rule_id="NEWS2_PARTIAL_SCORE",
            reading_time=reading_time,
        )

    def test_alert_is_deduplicated_until_push_delivery_is_recorded(self):
        alert_id, created, push_sent = self.create_alert()
        self.assertTrue(created)
        self.assertFalse(push_sent)
        self.assertEqual(pending_push_alert_ids(), [alert_id])

        duplicate_id, duplicate_created, duplicate_push_sent = self.create_alert()
        self.assertEqual(duplicate_id, alert_id)
        self.assertFalse(duplicate_created)
        self.assertFalse(duplicate_push_sent)

        mark_alert_push_sent(alert_id)
        self.assertEqual(pending_push_alert_ids(), [])

    def test_alert_can_be_acknowledged_and_subscription_is_upserted(self):
        alert_id, _, _ = self.create_alert()
        self.assertTrue(acknowledge_alert(alert_id))
        self.assertFalse(acknowledge_alert(alert_id))
        self.assertEqual(list_alerts()[0]["acknowledged_at"] is not None, True)

        subscription = {
            "endpoint": "https://push.example.test/subscription",
            "keys": {"auth": "auth-key", "p256dh": "public-key"},
        }
        save_subscription(subscription)
        save_subscription(subscription)
        self.assertEqual(list_subscriptions(), [subscription])

    def test_push_payload_does_not_include_patient_details(self):
        subscription = {
            "endpoint": "https://push.example.test/subscription",
            "keys": {"auth": "auth-key", "p256dh": "public-key"},
        }
        save_subscription(subscription)
        private_key = base64.b64encode(b"test-private-key").decode("ascii")
        with patch.dict(
            os.environ,
            {
                "MINEARENA_VAPID_PRIVATE_KEY_B64": private_key,
                "MINEARENA_VAPID_SUBJECT": "mailto:admin@example.test",
            },
        ), patch("services.web_push.webpush") as send:
            self.assertEqual(send_alert_notification(47), 1)

        payload = json.loads(send.call_args.kwargs["data"])
        self.assertEqual(payload, {"type": "new-alert", "alertId": 47})
        self.assertNotIn("patient_name", payload)


if __name__ == "__main__":
    unittest.main()
