"""Fake patients and fake vitals so the dashboard works before the backend exists.
Later we replace these with real data from Member 3's API."""
import random
from datetime import datetime, timedelta

import pandas as pd

# Synthetic demo patients. Member 3 / Synthea will provide the real ones later.
PATIENTS = {
    "P-001": {"name": "Ramesh", "age": 62, "sex": "Male",
              "conditions": ["Type 2 diabetes", "Hypertension"],
              "medications": ["Metformin", "Amlodipine"],
              "scale2": False, "base_spo2": 97.0},
    "P-002": {"name": "Sunita", "age": 68, "sex": "Female",
              "conditions": ["COPD", "Chronic hypercapnic respiratory failure"],
              "medications": ["Tiotropium inhaler", "Furosemide"],
              "scale2": True, "base_spo2": 91.0},
    "P-003": {"name": "Arjun", "age": 55, "sex": "Male",
              "conditions": ["Heart failure"],
              "medications": ["Bisoprolol (beta-blocker)", "Furosemide"],
              "scale2": False, "base_spo2": 96.0},
}


def generate_initial_data(base_spo2=96.0, points=60):
    """60 stable readings, one every 5 seconds, ending now."""
    now = datetime.now()
    rows = []
    for i in range(points):
        rows.append({
            "timestamp": now - timedelta(seconds=(points - i) * 5),
            "heart_rate": 78 + random.uniform(-3, 3),
            "spo2": base_spo2 + random.uniform(-1, 1),
            "respiratory_rate": 16 + random.uniform(-1, 1),
            "temperature": 36.8 + random.uniform(-0.2, 0.2),
        })
    return pd.DataFrame(rows)


def _append(df, rows):
    return pd.concat([df, pd.DataFrame(rows)], ignore_index=True).tail(180)


def apply_gradual_deterioration(df, steps=25):
    """SpO2 slowly falls, respiratory rate and heart rate slowly rise."""
    last = df.iloc[-1]
    hr, spo2, rr, temp, ts = (last["heart_rate"], last["spo2"],
                              last["respiratory_rate"], last["temperature"],
                              last["timestamp"])
    rows = []
    for _ in range(steps):
        ts = ts + timedelta(seconds=5)
        hr += random.uniform(0.4, 1.0)
        spo2 -= random.uniform(0.1, 0.3)
        rr += random.uniform(0.1, 0.35)
        temp += random.uniform(0, 0.03)
        rows.append({"timestamp": ts, "heart_rate": hr, "spo2": spo2,
                     "respiratory_rate": rr, "temperature": temp})
    return _append(df, rows)


def apply_sudden_spike(df):
    """One-off jump in heart rate and respiratory rate."""
    last = df.iloc[-1]
    row = {"timestamp": last["timestamp"] + timedelta(seconds=5),
           "heart_rate": last["heart_rate"] + 40,
           "spo2": last["spo2"],
           "respiratory_rate": last["respiratory_rate"] + 10,
           "temperature": last["temperature"]}
    return _append(df, [row])


def apply_probe_removal(df, steps=6):
    """Probe removal: SpO2 = 0 and heart rate flatlines at 0."""
    last = df.iloc[-1]
    rows = []
    ts = last["timestamp"]
    for _ in range(steps):
        ts = ts + timedelta(seconds=5)
        rows.append({"timestamp": ts, "heart_rate": 0, "spo2": 0,
                     "respiratory_rate": last["respiratory_rate"],
                     "temperature": last["temperature"]})
    return _append(df, rows)