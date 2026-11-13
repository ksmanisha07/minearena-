def check_artifact(reading):
    issues = []

    heart_rate = reading.get("heart_rate")
    spo2 = reading.get("spo2")
    respiratory_rate = reading.get("respiratory_rate")
    temperature = reading.get("temperature")

    # Impossible values
    if heart_rate is not None and (heart_rate < 0 or heart_rate > 250):
        issues.append("Heart rate outside possible range")

    if spo2 is not None and (spo2 < 0 or spo2 > 100):
        issues.append("SpO2 outside possible range")

    if respiratory_rate is not None and (respiratory_rate < 0 or respiratory_rate > 80):
        issues.append("Respiratory rate outside possible range")

    if temperature is not None and (temperature < 25 or temperature > 45):
        issues.append("Temperature outside possible range")

    # Probe removal pattern:
    # SpO2 becomes zero/null while heart rate flatlines
    if (spo2 in [0, None]) and (heart_rate in [0, None]):
        issues.append("Possible pulse-oximeter probe removal")

    if len(issues) > 0:
        return {
            "status": "ARTIFACT",
            "issues": issues,
            "confidence": 0.9,
            "recommended_action": "Check sensor placement and device connection"
        }

    return {
        "status": "CLEAN",
        "issues": [],
        "confidence": 1.0,
        "recommended_action": "Continue monitoring"
    }