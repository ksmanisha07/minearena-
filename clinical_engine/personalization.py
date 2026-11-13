def get_patient_rules(patient_profile):
    conditions = [condition.lower() for condition in patient_profile.get("conditions", [])]
    medications = [medication.lower() for medication in patient_profile.get("medications", [])]

    rules = {
        "spo2_rule": "SCALE_1",
        "spo2_target_range": [94, 100],
        "risk_conditions": [],
        "medication_context": []
    }

    if "hypercapnic respiratory failure" in conditions:
        rules["spo2_rule"] = "SCALE_2"
        rules["spo2_target_range"] = [88, 92]
        rules["risk_conditions"].append("Hypercapnic respiratory failure")

    if "copd" in conditions:
        rules["risk_conditions"].append("COPD")

    if "beta blocker" in " ".join(medications):
        rules["medication_context"].append(
            "Beta-blocker may blunt heart-rate response"
        )

    return rules


def get_spo2_rule(patient_profile):
    rules = get_patient_rules(patient_profile)
    return rules["spo2_rule"]