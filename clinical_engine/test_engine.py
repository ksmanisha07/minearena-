from engine import PatientMonitor

patient_profile = {
    "patient_id": "P-002",
    "name": "Sunita",
    "age": 68,
    "conditions": [
        "COPD",
        "Hypercapnic respiratory failure"
    ],
    "medications": [
        "Inhaler"
    ]
}

monitor = PatientMonitor("P-002", patient_profile)

# Normal readings
for spo2 in [97, 97, 96, 96, 96, 95, 95, 94, 94, 93]:
    reading = {
        "patient_id": "P-002",
        "timestamp": "2026-11-12T20:30:00",
        "heart_rate": 82,
        "spo2": spo2,
        "respiratory_rate": 18,
        "temperature": 36.8
    }

    result = monitor.process_reading(reading)
    print(result["alert_level"], "-", result["message"])

# Probe removal
probe_removal_reading = {
    "patient_id": "P-002",
    "timestamp": "2026-11-12T20:40:00",
    "heart_rate": 0,
    "spo2": 0,
    "respiratory_rate": 18,
    "temperature": 36.8
}

result = monitor.process_reading(probe_removal_reading)
print(result["alert_level"], "-", result["message"])