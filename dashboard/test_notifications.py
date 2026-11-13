import os
import tempfile
import unittest
from unittest.mock import patch

from notifications import (
    create_notification,
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
    seed_demo_notifications,
    unread_count,
)


class NotificationStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temp_dir.name, "notifications.sqlite3")
        self.environment = patch.dict(
            os.environ, {"MINEARENA_NOTIFICATION_DB": self.database_path}
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.addCleanup(self.temp_dir.cleanup)

    def create_alert(self, reading_time="2026-11-13T00:00:00"):
        return create_notification(
            patient_id="P-001",
            patient_name="Ramesh",
            severity="Urgent",
            message="Urgent: review needed",
            recommended_action="Immediate clinical review",
            rule_id="NEWS2_PARTIAL_SCORE",
            reading_time=reading_time,
        )

    def test_notification_persists_until_acknowledged(self):
        self.assertTrue(self.create_alert())
        self.assertEqual(unread_count(), 1)

        notification = list_notifications()[0]
        self.assertEqual(notification["severity"], "Urgent")
        mark_notification_read(notification["id"])

        self.assertEqual(unread_count(), 0)
        self.assertIsNotNone(list_notifications()[0]["read_at"])

    def test_reruns_do_not_duplicate_the_same_alert_event(self):
        self.assertTrue(self.create_alert())
        self.assertFalse(self.create_alert())
        self.assertEqual(len(list_notifications()), 1)

    def test_alerts_are_ordered_by_severity(self):
        self.create_alert()
        create_notification(
            "P-002", "Sunita", "Watch", "Watch alert", "Re-check", "TREND_RULE",
            "2026-11-13T00:01:00",
        )
        create_notification(
            "P-003", "Arjun", "Review", "Review alert", "Nurse review", "SCORE_RULE",
            "2026-11-13T00:02:00",
        )

        self.assertEqual(
            [item["severity"] for item in list_notifications()],
            ["Urgent", "Review", "Watch"],
        )

    def test_mark_all_notifications_read(self):
        self.create_alert()
        create_notification(
            "P-002", "Sunita", "Watch", "Watch alert", "Re-check", "TREND_RULE",
            "2026-11-13T00:01:00",
        )

        mark_all_notifications_read()

        self.assertEqual(unread_count(), 0)

    def test_demo_alerts_cover_each_severity_and_only_seed_once(self):
        self.assertEqual(seed_demo_notifications(), 4)
        self.assertEqual(seed_demo_notifications(), 0)
        self.assertEqual(
            [item["severity"] for item in list_notifications()],
            ["Urgent", "Review", "Watch", "Sensor issue"],
        )


if __name__ == "__main__":
    unittest.main()
