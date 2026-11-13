from datetime import datetime
import pandas as pd
import streamlit as st

from mock_data import (PATIENTS, apply_gradual_deterioration, apply_probe_removal,
                       apply_sudden_spike, generate_initial_data)
from scoring_mock import evaluate

st.set_page_config(page_title="Post-Discharge Deterioration Monitor", page_icon="🩺", layout="wide")
st.title("🩺 Post-Discharge Deterioration Monitor")
st.warning("Clinical decision support only. This system does not provide a medical diagnosis.")

# session_state keeps data between button clicks (Streamlit re-runs this file every click)
if "vitals" not in st.session_state:
    st.session_state.vitals = {pid: generate_initial_data(p["base_spo2"]) for pid, p in PATIENTS.items()}
if "checkins" not in st.session_state:
    st.session_state.checkins = []

# ---------- Sidebar: patient + scenario buttons ----------
pid = st.sidebar.selectbox("Select patient", list(PATIENTS),
                           format_func=lambda x: f"{x} — {PATIENTS[x]['name']}")
patient = PATIENTS[pid]
st.sidebar.header("Scenario controls (demo)")
if st.sidebar.button("Gradual deterioration"):
    st.session_state.vitals[pid] = apply_gradual_deterioration(st.session_state.vitals[pid])
if st.sidebar.button("Sudden spike"):
    st.session_state.vitals[pid] = apply_sudden_spike(st.session_state.vitals[pid])
if st.sidebar.button("Probe removal"):
    st.session_state.vitals[pid] = apply_probe_removal(st.session_state.vitals[pid])
if st.sidebar.button("Reset patient"):
    st.session_state.vitals[pid] = generate_initial_data(patient["base_spo2"])

df = st.session_state.vitals[pid]
result = evaluate(df, patient)
# ---------- Record alerts in history ----------
if "alert_log" not in st.session_state:
    st.session_state.alert_log = []
    st.session_state.last_level = {}
if result["level"] != "None" and st.session_state.last_level.get(pid) != result["level"]:
    st.session_state.alert_log.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "patient": f"{pid} {patient['name']}",
        "level": result["level"],
        "rule": result["rule_id"],
        "reason": result["trend"],
    })
st.session_state.last_level[pid] = result["level"]

# ---------- Top row ----------
c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("Patient profile")
    st.write(f"**{patient['name']}**, {patient['age']}, {patient['sex']}")
    st.write("**Conditions:** " + ", ".join(patient["conditions"]))
    st.write("**Medications:** " + ", ".join(patient["medications"]))
with c2:
    st.subheader("Current status")
    st.metric("NEWS2-style score (partial)", "n/a" if result["score"] is None else result["score"])
    st.metric("Alert level", result["level"])
with c3:
    st.subheader("Data quality")
    st.metric("Signal status", result["artifact_status"])
    st.caption("Score uses HR, SpO2, resp. rate, temperature only. BP and consciousness are unavailable.")

# ---------- Alert explanation ----------
st.subheader("Latest alert")
if result["level"] == "Urgent":
    st.error(result["message"])
elif result["level"] == "Review":
    st.warning(result["message"])
elif result["level"] == "Watch":
    st.info(result["message"])
elif result["level"] == "Sensor issue":
    st.info("🔧 " + result["message"])
else:
    st.success("No active clinical alert.")
with st.expander("Why this alert?", expanded=result["level"] != "None"):
    st.markdown(f"**Reading:** {result['trigger_reading']}")
    st.markdown(f"**Rule applied:** `{result['rule_id']}`")
    st.markdown(f"**Patient profile fact:** {result['patient_factor']}")
    st.markdown(f"**Trend:** {result['trend']}")
    st.markdown(f"**Data quality:** {result['artifact_status']}")
    st.markdown(f"**Suggested action:** {result['recommended_action']}")

# ---------- Charts ----------
st.subheader("Vital signs")
chart_df = df.set_index("timestamp")
a, b = st.columns(2)
a.caption("Heart rate (/min)");            a.line_chart(chart_df[["heart_rate"]], height=220)
b.caption("SpO2 (%)");                     b.line_chart(chart_df[["spo2"]], height=220)
c, d = st.columns(2)
c.caption("Respiratory rate (/min)");      c.line_chart(chart_df[["respiratory_rate"]], height=220)
d.caption("Temperature (°C)");             d.line_chart(chart_df[["temperature"]], height=220)

# ---------- Alert history ----------
st.subheader("Alert history")
if st.session_state.alert_log:
    st.dataframe(pd.DataFrame(st.session_state.alert_log[::-1]), hide_index=True)
else:
    st.info("No alerts yet. Click a scenario button in the sidebar.")
    # ---------- Symptom check-in ----------
st.subheader("Patient symptom check-in")
with st.form("checkin"):
    sx = {name: st.slider(name, 0, 10, 0)
          for name in ["Breathlessness", "Fever", "Dizziness", "Chest pain", "Reduced activity"]}
    if st.form_submit_button("Submit check-in"):
        st.session_state.checkins.append({"patient": pid, **sx})
        st.success("Saved locally. It will be sent to the backend once the API is ready.")
if st.session_state.checkins:
    st.dataframe(pd.DataFrame(st.session_state.checkins))

# ---------- Performance report (placeholder) ----------
st.subheader("Performance report vs fixed-threshold monitoring")
st.info("Placeholder. These numbers will be computed from the team's replay log, never typed in by hand.")
st.dataframe(pd.DataFrame({
    "Metric": ["Detection lead time", "Alerts per patient-day", "False alerts", "Artifact alerts suppressed"],
    "Our monitor": ["—", "—", "—", "—"],
    "Fixed threshold": ["—", "—", "—", "—"],
}), hide_index=True)