"""TEMPORARY scoring used only to make the dashboard react to the demo buttons.
Member 2's real engine replaces this. NEWS2-style = partial score from 4 vitals only
(no blood pressure / consciousness / oxygen-use data)."""


def _rr(v):
    return 3 if v <= 8 else 1 if v <= 11 else 0 if v <= 20 else 2 if v <= 24 else 3


def _spo2_scale1(v):
    return 3 if v <= 91 else 2 if v <= 93 else 1 if v <= 95 else 0


def _spo2_scale2(v):  # room air only; oxygen status is unknown in this prototype
    return 3 if v <= 83 else 2 if v <= 85 else 1 if v <= 87 else 0


def _temp(v):
    return 3 if v <= 35.0 else 1 if v <= 36.0 else 0 if v <= 38.0 else 1 if v <= 39.0 else 2


def _hr(v):
    return 3 if v <= 40 else 1 if v <= 50 else 0 if v <= 90 else 1 if v <= 110 else 2 if v <= 130 else 3


def evaluate(df, patient):
    last = df.iloc[-1]
    recent = df.tail(3)
    if (recent["spo2"] <= 0).all() and (recent["heart_rate"] <= 0).all():
        return {
            "score": None, "level": "Sensor issue", "artifact_status": "ARTIFACT",
            "message": "Probable probe removal. Clinical alert suppressed.",
            "trigger_reading": {"spo2": 0, "heart_rate": 0},
            "rule_id": "PROBE_REMOVAL_SIGNATURE",
            "patient_factor": "Not applicable (device problem, not a clinical finding)",
            "trend": "SpO2 = 0 and heart rate flatlined for 3+ readings",
            "recommended_action": "Ask patient to refit the sensor; verify with another measurement",
        }
    hr, spo2, rr, temp = (round(last["heart_rate"]), round(last["spo2"]),
                          round(last["respiratory_rate"]), round(last["temperature"], 1))
    scale2 = patient["scale2"]
    parts = {"Heart rate": _hr(hr), "SpO2": (_spo2_scale2 if scale2 else _spo2_scale1)(spo2),
             "Resp. rate": _rr(rr), "Temperature": _temp(temp)}
    total = sum(parts.values())
    level = ("Urgent" if total >= 7 else "Review" if total >= 5 or max(parts.values()) == 3
             else "Watch" if total >= 2 else "None")
    rule = "NEWS2_PARTIAL_SCORE"
    baseline = df.head(20)["spo2"].median()
    drop = baseline - spo2
    trend = f"SpO2 is {drop:.1f} points vs this patient's baseline ({baseline:.0f}%)"
    if level == "None" and drop >= 3:
        level, rule = "Watch", "SPO2_TREND_BELOW_BASELINE"
    factor = ("Chronic hypercapnic respiratory failure: SpO2 Scale 2 (target 88-92%)" if scale2
              else "No Scale 2 indication documented: standard SpO2 Scale 1")
    actions = {"Urgent": "Immediate clinical review", "Review": "Nurse review within 15 minutes",
               "Watch": "Keep watching; re-check in 30 minutes", "None": "No action needed"}
    return {
        "score": total, "components": parts, "level": level, "artifact_status": "CLEAN",
        "message": f"{level}: partial NEWS2-style score {total}",
        "trigger_reading": {"heart_rate": hr, "spo2": spo2, "respiratory_rate": rr, "temperature": temp},
        "rule_id": rule, "patient_factor": factor, "trend": trend,
        "recommended_action": actions[level],
    }