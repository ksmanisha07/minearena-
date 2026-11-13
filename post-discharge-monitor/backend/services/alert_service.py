import uuid
from datetime import datetime

class AlertService:
    def __init__(self):
        self.alerts = {}

    def create_alert(self, patient_id: str, alert: dict):
        alert_id = str(uuid.uuid4())

        structured_alert = {
            "alert_id": alert_id,
            "patient_id": patient_id,
            "created_at": datetime.utcnow().isoformat(),
            "alert_level": alert.get("alert_level", "Watch"),
            "message": alert.get("message"),
            "trigger_reading": alert.get("trigger_reading"),
            "rule_id": alert.get("rule_id"),
            "patient_factor": alert.get("patient_factor"),
            "trend": alert.get("trend"),
            "artifact_status": alert.get("artifact_status", "CLEAN"),
            "recommended_action": alert.get("recommended_action"),
            "status": "active"
        }

        if patient_id not in self.alerts:
            self.alerts[patient_id] = []

        self.alerts[patient_id].append(structured_alert)
        return structured_alert

    def get_alerts(self, patient_id: str):
        return {
            "patient_id": patient_id,
            "alerts": self.alerts.get(patient_id, [])
        }