SUPPORTED_VITALS = {
    "8867-4": {
        "name": "Heart rate",
        "unit": "/min",
        "unit_system": "http://unitsofmeasure.org"
    },
    "2708-6": {
        "name": "Oxygen saturation",
        "unit": "%",
        "unit_system": "http://unitsofmeasure.org"
    },
    "9279-1": {
        "name": "Respiratory rate",
        "unit": "/min",
        "unit_system": "http://unitsofmeasure.org"
    },
    "8310-5": {
        "name": "Body temperature",
        "unit": "Cel",
        "unit_system": "http://unitsofmeasure.org"
    }
}

def validate_observation(observation: dict):
    errors = []

    if observation.get("resourceType") != "Observation":
        errors.append("resourceType must be Observation")

    if observation.get("status") not in ["final", "preliminary", "entered-in-error"]:
        errors.append("Invalid or missing Observation status")

    category = observation.get("category", [])
    if not any(c.get("coding", [{}])[0].get("code") == "vital-signs" for c in category):
        errors.append("Observation must include vital-signs category")

    code = observation.get("code", {})
    loinc_code = None

    for coding in code.get("coding", []):
        if coding.get("system") == "http://loinc.org":
            loinc_code = coding.get("code")

    if not loinc_code:
        errors.append("Missing LOINC coding")

    if loinc_code not in SUPPORTED_VITALS:
        errors.append(f"Unsupported LOINC code: {loinc_code}")

    if not observation.get("subject", {}).get("reference"):
        errors.append("Missing patient reference")

    if not observation.get("effectiveDateTime"):
        errors.append("Missing effectiveDateTime")

    value_quantity = observation.get("valueQuantity", {})

    if not value_quantity.get("value") and value_quantity.get("value") != 0:
        errors.append("Missing numeric value")

    if loinc_code in SUPPORTED_VITALS:
        expected_unit = SUPPORTED_VITALS[loinc_code]["unit"]
        if value_quantity.get("unit") != expected_unit:
            errors.append(f"Expected unit {expected_unit}")

    return errors