import time
import random
import json
import requests
from datetime import datetime, timezone

API_URL = "http://127.0.0.1:8000/fhir/Observation"
PATIENT_ID = "P-001"
DRY_RUN = True

BASELINE = {
    "heart_rate": 78,
    "spo2": 96,
    "respiratory_rate": 16,
    "temperature": 36.8,
}

LOINC_CODES = {
    "heart_rate": "8867-4",
    "spo2": "2708-6",
    "respiratory_rate": "9279-1",
    "temperature": "8310-5",
}

UNITS = {
    "heart_rate": "/min",
    "spo2": "%",
    "respiratory_rate": "/min",
    "temperature": "Cel",
}


def create_observation(vital_type, value, patient_id):
    return {
        "resourceType": "Observation",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": LOINC_CODES[vital_type],
                    "display": vital_type.replace("_", " ").title()
                }
            ]
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "effectiveDateTime": datetime.now(timezone.utc).isoformat(),
        "valueQuantity": {
            "value": round(value, 2),
            "unit": UNITS[vital_type],
            "system": "http://unitsofmeasure.org",
            "code": UNITS[vital_type]
        }
    }


def send_reading(vital_type, value, patient_id):
    observation = create_observation(vital_type, value, patient_id)

    if DRY_RUN:
        print(
            f"[DRY RUN] {patient_id} | "
            f"{vital_type}: {value:.2f} | Not sent to backend"
        )
        return

    try:
        response = requests.post(
            API_URL,
            json=observation,
            timeout=5
        )
        response.raise_for_status()

        print(
            f"{patient_id} | {vital_type}: {value:.2f} | "
            f"HTTP {response.status_code}"
        )

    except requests.exceptions.RequestException as error:
        print(f"Backend unavailable: {error}")

        
def send_all_vitals(values, patient_id):
    for vital_type, value in values.items():
        send_reading(vital_type, value, patient_id)


def stable_values():
    return {
        "heart_rate": BASELINE["heart_rate"] + random.uniform(-3, 3),
        "spo2": BASELINE["spo2"] + random.uniform(-1, 1),
        "respiratory_rate": BASELINE["respiratory_rate"] + random.uniform(-1, 1),
        "temperature": BASELINE["temperature"] + random.uniform(-0.2, 0.2),
    }


def gradual_deterioration_values(step, total_steps):
    progress = step / total_steps

    return {
        "heart_rate": BASELINE["heart_rate"] + progress * 20,
        "spo2": BASELINE["spo2"] - progress * 8,
        "respiratory_rate": BASELINE["respiratory_rate"] + progress * 10,
        "temperature": BASELINE["temperature"] + progress * 1.2,
    }


def sudden_spike_values():
    return {
        "heart_rate": BASELINE["heart_rate"] + random.uniform(25, 40),
        "spo2": BASELINE["spo2"] + random.uniform(-1, 1),
        "respiratory_rate": BASELINE["respiratory_rate"] + random.uniform(2, 5),
        "temperature": BASELINE["temperature"],
    }


def motion_noise_values():
    return {
        "heart_rate": BASELINE["heart_rate"] + random.uniform(-15, 15),
        "spo2": BASELINE["spo2"] + random.uniform(-4, 4),
        "respiratory_rate": BASELINE["respiratory_rate"] + random.uniform(-4, 4),
        "temperature": BASELINE["temperature"] + random.uniform(-0.5, 0.5),
    }


def probe_removal_values():
    return {
        "heart_rate": 0,
        "spo2": 0,
        "respiratory_rate": BASELINE["respiratory_rate"],
        "temperature": BASELINE["temperature"],
    }


def run_scenario(scenario_name, patient_id, interval_seconds=5):
    with open("scenarios.json", "r") as file:
        scenarios = json.load(file)

    if scenario_name not in scenarios:
        print("Unknown scenario")
        return

    duration = scenarios[scenario_name]["duration_seconds"]
    total_steps = int(duration / interval_seconds)

    print(f"Starting scenario: {scenario_name}")

    for step in range(total_steps):
        if scenario_name == "stable_recovery":
            values = stable_values()

        elif scenario_name == "gradual_deterioration":
            values = gradual_deterioration_values(step, total_steps)

        elif scenario_name == "sudden_spike":
            values = sudden_spike_values()

        elif scenario_name == "motion_noise":
            values = motion_noise_values()

        elif scenario_name == "probe_removal":
            values = probe_removal_values()

        elif scenario_name == "data_dropout":
            print("No data sent — simulating connectivity loss")
            time.sleep(interval_seconds)
            continue

        send_all_vitals(values, patient_id)
        time.sleep(interval_seconds)

    print(f"Scenario completed: {scenario_name}")


if __name__ == "__main__":
    run_scenario("gradual_deterioration", PATIENT_ID)