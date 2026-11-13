import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


class MobileApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.environment = patch.dict(
            os.environ,
            {
                "MINEARENA_MOBILE_DB": os.path.join(self.temp_dir.name, "mobile.sqlite3"),
                "MINEARENA_DOCTOR_ACCESS_TOKEN": "doctor-test-token",
                "MINEARENA_ALERT_INGEST_TOKEN": "ingest-test-token",
            },
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.addCleanup(self.temp_dir.cleanup)
        self.client = TestClient(app)
        self.doctor_headers = {"Authorization": "Bearer doctor-test-token"}

    def test_mobile_page_is_served_and_doctor_endpoints_require_sign_in(self):
        page = self.client.get("/mobile/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Alert inbox", page.text)
        self.assertEqual(self.client.get("/api/mobile/doctor/alerts").status_code, 401)
        self.assertEqual(
            self.client.post(
                "/api/mobile/doctor/session", headers=self.doctor_headers
            ).json(),
            {"authenticated": True},
        )

    def test_new_monitor_alert_is_persisted_and_sent_once(self):
        payload = {
            "patient_id": "P-001",
            "patient_name": "Ramesh",
            "severity": "Urgent",
            "message": "Urgent review needed",
            "recommended_action": "Immediate clinical review",
            "rule_id": "NEWS2_PARTIAL_SCORE",
            "reading_time": "2026-11-13T00:00:00",
        }
        with patch("api.mobile.send_alert_notification", return_value=1) as send_push:
            response = self.client.post(
                "/api/mobile/alerts",
                headers={"X-Alert-Ingest-Token": "ingest-test-token"},
                json=payload,
            )
            duplicate = self.client.post(
                "/api/mobile/alerts",
                headers={"X-Alert-Ingest-Token": "ingest-test-token"},
                json=payload,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["push_delivered"], 1)
        self.assertFalse(duplicate.json()["created"])
        self.assertEqual(duplicate.json()["push_status"], "already_sent")
        self.assertEqual(send_push.call_count, 1)
        alerts = self.client.get(
            "/api/mobile/doctor/alerts", headers=self.doctor_headers
        ).json()["alerts"]
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["patient_id"], "P-001")
        acknowledged = self.client.patch(
            f"/api/mobile/doctor/alerts/{alerts[0]['id']}/acknowledge",
            headers=self.doctor_headers,
        )
        self.assertEqual(acknowledged.status_code, 200)

    def test_every_alert_severity_is_accepted_for_push(self):
        severities = ["Urgent", "Review", "Watch", "Sensor issue"]
        with patch("api.mobile.send_alert_notification", return_value=1) as send_push:
            for index, severity in enumerate(severities):
                response = self.client.post(
                    "/api/mobile/alerts",
                    headers={"X-Alert-Ingest-Token": "ingest-test-token"},
                    json={
                        "patient_id": f"P-{index:03d}",
                        "patient_name": "Synthetic",
                        "severity": severity,
                        "message": f"Synthetic {severity} alert",
                        "recommended_action": "Review synthetic test alert",
                        "rule_id": f"TEST_{index}",
                        "reading_time": f"2026-11-13T00:0{index}:00",
                    },
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["push_status"], "sent")

        self.assertEqual(send_push.call_count, len(severities))


if __name__ == "__main__":
    unittest.main()
