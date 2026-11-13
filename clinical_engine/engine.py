import time
from collections import deque
from scoring import calculate_news_style_score
from personalization import get_patient_rules
from artifact_detector import check_artifact
from alert_engine import decide_alert


class PatientMonitor:
    def __init__(self, patient_id, patient_profile):
        self.patient_id = patient_id
        self.patient_profile = patient_profile

        self.heart_rate_history = deque(maxlen=120)
        self.spo2_history = deque(maxlen=120)
        self.respiratory_rate_history = deque(maxlen=120)
        self.temperature_history = deque(maxlen=120)

        self.current_alert = "NONE"
        self.current_score = 0

    def process_reading(self, reading):
        artifact_result = check_artifact(reading)

        if artifact_result["status"] == "ARTIFACT":
            return {
                "patient_id": self.patient_id,
                "alert_level": "DEVICE_ISSUE",
                "message": "Sensor reading may be unreliable.",
                "artifact_status": "ARTIFACT",
                "details": artifact_result,
                "score": self.current_score
            }

        self.heart_rate_history.append(reading["heart_rate"])
        self.spo2_history.append(reading["spo2"])
        self.respiratory_rate_history.append(reading["respiratory_rate"])
        self.temperature_history.append(reading["temperature"])

        score_result = calculate_news_style_score(reading, self.patient_profile)

        self.current_score = score_result["score"]

        alert_result = decide_alert(
            reading=reading,
            score_result=score_result,
            patient_profile=self.patient_profile,
            spo2_history=list(self.spo2_history),
            respiratory_rate_history=list(self.respiratory_rate_history),
            heart_rate_history=list(self.heart_rate_history)
        )

        self.current_alert = alert_result["alert_level"]

        return {
            "patient_id": self.patient_id,
            "alert_level": self.current_alert,
            "message": alert_result["message"],
            "rule_id": alert_result["rule_id"],
            "patient_factor": alert_result["patient_factor"],
            "trend": alert_result["trend"],
            "artifact_status": artifact_result["status"],
            "recommended_action": alert_result["recommended_action"],
            "score": self.current_score,
            "score_details": score_result
        }