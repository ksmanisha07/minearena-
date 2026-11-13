from personalization import get_spo2_rule
def calculate_news_style_score(reading, patient_profile):
    score = 0
    details = {}

    respiratory_rate = reading["respiratory_rate"]
    spo2 = reading["spo2"]
    heart_rate = reading["heart_rate"]
    temperature = reading["temperature"]

    # Respiratory rate
    if respiratory_rate <= 8:
        rr_score = 3
    elif respiratory_rate <= 11:
        rr_score = 1
    elif respiratory_rate <= 20:
        rr_score = 0
    elif respiratory_rate <= 24:
        rr_score = 2
    else:
        rr_score = 3

    score += rr_score
    details["respiratory_rate"] = {
        "value": respiratory_rate,
        "score": rr_score
    }

    # Oxygen saturation
    spo2_rule = get_spo2_rule(patient_profile)

    if spo2_rule == "SCALE_2":
        if spo2 <= 83:
            spo2_score = 3
        elif spo2 <= 85:
            spo2_score = 2
        elif spo2 <= 87:
            spo2_score = 1
        elif spo2 <= 92:
            spo2_score = 0
        else:
            spo2_score = 3
    else:
        if spo2 <= 91:
            spo2_score = 3
        elif spo2 <= 93:
            spo2_score = 2
        elif spo2 <= 95:
            spo2_score = 1
        else:
            spo2_score = 0

    score += spo2_score
    details["spo2"] = {
        "value": spo2,
        "score": spo2_score,
        "rule_used": spo2_rule
    }

    # Heart rate / pulse
    if heart_rate <= 40:
        hr_score = 3
    elif heart_rate <= 50:
        hr_score = 1
    elif heart_rate <= 90:
        hr_score = 0
    elif heart_rate <= 110:
        hr_score = 1
    elif heart_rate <= 130:
        hr_score = 2
    else:
        hr_score = 3

    score += hr_score
    details["heart_rate"] = {
        "value": heart_rate,
        "score": hr_score
    }

    # Temperature
    if temperature <= 35.0:
        temperature_score = 3
    elif temperature <= 36.0:
        temperature_score = 1
    elif temperature <= 38.0:
        temperature_score = 0
    elif temperature <= 39.0:
        temperature_score = 1
    else:
        temperature_score = 2

    score += temperature_score
    details["temperature"] = {
        "value": temperature,
        "score": temperature_score
    }

    return {
        "score": score,
        "details": details,
        "score_type": "NEWS2-style partial score",
        "missing_components": [
            "systolic_blood_pressure",
            "consciousness",
            "supplemental_oxygen_status"
        ]
    }