from personalization import get_patient_rules
import statistics


def calculate_baseline(values):
    if len(values) < 10:
        return None

    recent_values = values[-30:]
    return statistics.median(recent_values)


def calculate_trend(values):
    if len(values) < 10:
        return "NOT_ENOUGH_DATA"

    recent_values = values[-10:]
    earlier_values = values[-30:-10]

    if len(earlier_values) < 5:
        return "NOT_ENOUGH_DATA"

    recent_average = statistics.mean(recent_values)
    earlier_average = statistics.mean(earlier_values)

    difference = recent_average - earlier_average

    if difference > 1.5:
        return "RISING"
    elif difference < -1.5:
        return "FALLING"
    else:
        return "STABLE"


def decide_alert(
    reading,
    score_result,
    patient_profile,
    spo2_history,
    respiratory_rate_history,
    heart_rate_history
):
    score = score_result["score"]

    spo2_trend = calculate_trend(spo2_history)
    respiratory_trend = calculate_trend(respiratory_rate_history)

    spo2_baseline = calculate_baseline(spo2_history)
    respiratory_baseline = calculate_baseline(respiratory_rate_history)

    rules = get_patient_rules(patient_profile)

    spo2_target = rules["spo2_target_range"]

    # Urgent: high NEWS-style score
    if score >= 7:
        return {
            "alert_level": "URGENT",
            "message": "High deterioration risk detected.",
            "rule_id": "NEWS_STYLE_HIGH_SCORE",
            "patient_factor": ", ".join(rules["risk_conditions"]) or "General monitoring",
            "trend": f"SpO2 trend: {spo2_trend}; respiratory trend: {respiratory_trend}",
            "recommended_action": "Immediate clinical review"
        }

    # Review: moderate score or worsening trend
    if score >= 5:
        return {
            "alert_level": "REVIEW",
            "message": "Sustained deterioration pattern detected.",
            "rule_id": "NEWS_STYLE_MODERATE_SCORE",
            "patient_factor": ", ".join(rules["risk_conditions"]) or "General monitoring",
            "trend": f"SpO2 trend: {spo2_trend}; respiratory trend: {respiratory_trend}",
            "recommended_action": "Nurse review recommended"
        }

    # Personalized early warning
    if (
        spo2_baseline is not None
        and reading["spo2"] < spo2_baseline - 3
        and spo2_trend == "FALLING"
    ):
        return {
            "alert_level": "WATCH",
            "message": "SpO2 is falling below this patient’s personal baseline.",
            "rule_id": "PERSONALIZED_SPO2_TREND",
            "patient_factor": ", ".join(rules["risk_conditions"]) or "General monitoring",
            "trend": f"Current SpO2: {reading['spo2']}%; baseline: {spo2_baseline}%",
            "recommended_action": "Continue close monitoring"
        }

    if (
        respiratory_baseline is not None
        and reading["respiratory_rate"] > respiratory_baseline + 3
        and respiratory_trend == "RISING"
    ):
        return {
            "alert_level": "WATCH",
            "message": "Respiratory rate is rising above this patient’s personal baseline.",
            "rule_id": "PERSONALIZED_RESPIRATORY_TREND",
            "patient_factor": ", ".join(rules["risk_conditions"]) or "General monitoring",
            "trend": f"Current respiratory rate: {reading['respiratory_rate']}/min; baseline: {respiratory_baseline}/min",
            "recommended_action": "Continue close monitoring"
        }

    # SpO2 target check for Scale 2 patients
    if rules["spo2_rule"] == "SCALE_2":
        if reading["spo2"] < spo2_target[0]:
            return {
                "alert_level": "REVIEW",
                "message": "SpO2 is below the patient-specific target range.",
                "rule_id": "SCALE_2_TARGET_CHECK",
                "patient_factor": "Hypercapnic respiratory failure; target SpO2 88–92%",
                "trend": f"SpO2 trend: {spo2_trend}",
                "recommended_action": "Review oxygen status and patient condition"
            }

    return {
        "alert_level": "NONE",
        "message": "No concerning pattern detected.",
        "rule_id": "NO_ALERT",
        "patient_factor": ", ".join(rules["risk_conditions"]) or "General monitoring",
        "trend": f"SpO2 trend: {spo2_trend}; respiratory trend: {respiratory_trend}",
        "recommended_action": "Continue monitoring"
    }