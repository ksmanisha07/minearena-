from datetime import datetime
import hmac
from html import escape
import os

import altair as alt
import pandas as pd
import requests
import streamlit as st

from mock_data import (PATIENTS, apply_gradual_deterioration, apply_probe_removal,
                       apply_sudden_spike, generate_initial_data)
from notifications import (create_notification, list_notifications,
                           mark_all_notifications_read, mark_notification_read,
                           seed_demo_notifications, unread_count)
from scoring_mock import evaluate

st.set_page_config(page_title="Post-Discharge Monitor", page_icon="🩺", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --ink: #162f42;
        --muted: #64788a;
        --teal: #087f8c;
        --line: #e3ebf1;
    }
    .stApp {
        background:
            radial-gradient(ellipse at 82% 0%, rgba(80, 190, 197, .11), transparent 34rem),
            #f3f7fa;
        color: var(--ink);
    }
    .block-container {
        max-width: 1440px;
        padding: 1.8rem 2.2rem 3.5rem;
    }
    header[data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { visibility: hidden; height: 0; }
    #MainMenu, footer { visibility: hidden; }
    h1, h2, h3, p { color: var(--ink); }
    h2 { letter-spacing: -.025em; }
    section[data-testid="stSidebar"] {
        background: linear-gradient(165deg, #102c3c 0%, #16465a 100%);
    }
    section[data-testid="stSidebar"] * { color: #eef8fa; }
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        color: #c7dce3;
        font-size: .82rem;
        font-weight: 650;
    }
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"] {
        border: 1px solid rgba(255,255,255,.22) !important;
        border-radius: 12px !important;
        background: rgba(255,255,255,.1) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] {
        color: #eef8fa !important;
        background: transparent !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"] button {
        border: 0 !important;
        background: transparent !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] svg { fill: #d7edf0 !important; }
    [data-testid="stMain"] button[data-testid="stBaseButton-primary"] {
        border: 0 !important;
        color: #fff !important;
        background: linear-gradient(110deg, #087f8c, #145d73) !important;
        box-shadow: 0 7px 18px rgba(8,127,140,.18);
    }
    [data-testid="stMain"] button[data-testid="stBaseButton-primary"] * {
        color: #fff !important;
    }
    [data-testid="stMain"] button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(110deg, #066c78, #104c62) !important;
        box-shadow: 0 9px 22px rgba(8,127,140,.25);
        transform: translateY(-1px);
    }
    section[data-testid="stSidebar"] button {
        border: 1px solid rgba(255,255,255,.18);
        border-radius: 11px;
        background: rgba(255,255,255,.09);
        transition: background .15s ease, transform .15s ease;
    }
    section[data-testid="stSidebar"] button:hover {
        background: rgba(255,255,255,.18);
        border-color: rgba(255,255,255,.35);
        transform: translateY(-1px);
    }
    .hero {
        position: relative;
        overflow: hidden;
        padding: 1.8rem 2rem;
        margin-bottom: 1.15rem;
        border: 1px solid rgba(255,255,255,.16);
        border-radius: 24px;
        color: #f5ffff;
        background: linear-gradient(112deg, #103b50 0%, #087f8c 58%, #35a9a0 100%);
        box-shadow: 0 16px 38px rgba(13, 69, 87, .16);
    }
    .hero:after {
        content: "";
        position: absolute;
        width: 270px;
        height: 270px;
        right: 7%;
        top: -150px;
        border: 1px solid rgba(255,255,255,.18);
        border-radius: 50%;
        box-shadow: 0 0 0 34px rgba(255,255,255,.045), 0 0 0 70px rgba(255,255,255,.035);
    }
    .hero-kicker {
        margin: 0 0 .45rem;
        color: #bcebe6;
        font-size: .76rem;
        font-weight: 750;
        letter-spacing: .14em;
        text-transform: uppercase;
    }
    .hero h1 {
        margin: 0;
        color: white;
        font-size: clamp(1.7rem, 3vw, 2.35rem);
        letter-spacing: -.045em;
        line-height: 1.15;
    }
    .hero-subtitle {
        margin: .55rem 0 0;
        color: #e2f5f4;
        font-size: .98rem;
    }
    .demo-pill {
        position: absolute;
        z-index: 1;
        top: 1.6rem;
        right: 1.8rem;
        padding: .42rem .75rem;
        border: 1px solid rgba(255,255,255,.32);
        border-radius: 999px;
        color: #f1fffd;
        background: rgba(255,255,255,.12);
        font-size: .73rem;
        font-weight: 700;
        letter-spacing: .06em;
    }
    .disclaimer {
        margin: .8rem 0 1.4rem;
        padding: .72rem 1rem;
        border-left: 4px solid #e8ad4c;
        border-radius: 0 10px 10px 0;
        color: #71571f;
        background: #fff7e6;
        font-size: .87rem;
    }
    .section-heading {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 1rem;
        margin: 1.55rem 0 .8rem;
    }
    .section-heading h2 {
        margin: 0;
        font-size: 1.22rem;
        letter-spacing: -.025em;
    }
    .section-heading span {
        color: var(--muted);
        font-size: .82rem;
    }
    .profile-card {
        height: 100%;
        padding: 1.2rem 1.35rem;
        border: 1px solid var(--line);
        border-radius: 18px;
        background: rgba(255,255,255,.88);
        box-shadow: 0 7px 22px rgba(29, 66, 87, .045);
    }
    .profile-top {
        display: flex;
        align-items: center;
        gap: .85rem;
        margin-bottom: .95rem;
    }
    .avatar {
        display: grid;
        width: 48px;
        height: 48px;
        flex: 0 0 48px;
        place-items: center;
        border-radius: 15px;
        color: #087f8c;
        background: #ddf5f1;
        font-size: 1.2rem;
        font-weight: 800;
    }
    .profile-name { margin: 0; font-size: 1.12rem; font-weight: 750; }
    .profile-meta { margin: .16rem 0 0; color: var(--muted); font-size: .84rem; }
    .profile-label {
        margin: .8rem 0 .35rem;
        color: var(--muted);
        font-size: .72rem;
        font-weight: 750;
        letter-spacing: .08em;
        text-transform: uppercase;
    }
    .tag {
        display: inline-block;
        margin: .12rem .2rem .12rem 0;
        padding: .26rem .55rem;
        border: 1px solid #e4edf2;
        border-radius: 999px;
        color: #355468;
        background: #f5f9fb;
        font-size: .75rem;
    }
    div[data-testid="stMetric"] {
        min-height: 118px;
        padding: 1rem 1.1rem;
        border: 1px solid var(--line);
        border-radius: 17px;
        background: rgba(255,255,255,.92);
        box-shadow: 0 7px 22px rgba(29, 66, 87, .045);
    }
    div[data-testid="stMetricLabel"] p {
        color: var(--muted);
        font-size: .79rem;
        font-weight: 650;
    }
    div[data-testid="stMetricValue"] {
        color: var(--ink);
        font-size: 1.8rem;
        font-weight: 750;
    }
    .alert-card {
        display: flex;
        align-items: flex-start;
        gap: .9rem;
        padding: 1.05rem 1.2rem;
        border: 1px solid;
        border-radius: 16px;
    }
    .alert-icon {
        display: grid;
        width: 38px;
        height: 38px;
        flex: 0 0 38px;
        place-items: center;
        border-radius: 12px;
        background: rgba(255,255,255,.62);
        font-size: 1.2rem;
    }
    .alert-title { margin: 0 0 .18rem; font-weight: 750; }
    .alert-copy { margin: 0; font-size: .87rem; }
    .alert-action { margin: .4rem 0 0; font-size: .8rem; font-weight: 650; }
    .alert-none { border-color: #bde8d1; color: #176341; background: #eaf8f0; }
    .alert-watch { border-color: #f0d48b; color: #755413; background: #fff7df; }
    .alert-review { border-color: #f3c49e; color: #814315; background: #fff0e4; }
    .alert-urgent { border-color: #f0b5b8; color: #852d34; background: #fff0f0; }
    .alert-sensor { border-color: #c8c0f1; color: #514384; background: #f1efff; }
    .login-card {
        max-width: 520px;
        margin: 2rem auto;
        padding: 1.6rem;
        border: 1px solid var(--line);
        border-radius: 20px;
        background: rgba(255,255,255,.94);
        box-shadow: 0 12px 32px rgba(29,66,87,.08);
    }
    .notification-card { margin: .5rem 0 .85rem; }
    .notification-meta { margin: .4rem 0 0; font-size: .79rem; opacity: .8; }
    .notification-badge {
        display: inline-block;
        margin-bottom: .35rem;
        padding: .18rem .55rem;
        border-radius: 999px;
        font-size: .7rem;
        font-weight: 800;
        letter-spacing: .06em;
        text-transform: uppercase;
    }
    .badge-urgent { color: #852d34; background: #f8d7da; }
    .badge-review { color: #814315; background: #ffe2ca; }
    .badge-watch { color: #755413; background: #ffefbf; }
    .badge-sensor { color: #514384; background: #e3defb; }
    .severity-tile {
        display: flex;
        align-items: center;
        justify-content: space-between;
        min-height: 74px;
        margin-bottom: .8rem;
        padding: .8rem 1rem;
        border: 1px solid;
        border-radius: 15px;
        box-shadow: 0 5px 16px rgba(29,66,87,.045);
    }
    .severity-tile-label {
        font-size: .73rem;
        font-weight: 750;
        letter-spacing: .06em;
        text-transform: uppercase;
    }
    .severity-tile-count { font-size: 1.55rem; font-weight: 800; }
    .tile-urgent { border-color: #f0b5b8; color: #852d34; background: linear-gradient(120deg,#fff0f0,#fff9f9); }
    .tile-review { border-color: #f3c49e; color: #814315; background: linear-gradient(120deg,#fff0e4,#fffaf5); }
    .tile-watch { border-color: #f0d48b; color: #755413; background: linear-gradient(120deg,#fff7df,#fffdf5); }
    .tile-sensor { border-color: #c8c0f1; color: #514384; background: linear-gradient(120deg,#f1efff,#fbfaff); }
    .inbox-note {
        margin: .4rem 0 1rem;
        padding: .75rem 1rem;
        border: 1px solid #cfe5eb;
        border-radius: 12px;
        color: #37576b;
        background: #edf7f9;
        font-size: .84rem;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: .65rem .75rem .25rem;
        border: 1px solid var(--line) !important;
        border-radius: 18px !important;
        background: rgba(255,255,255,.92);
        box-shadow: 0 7px 22px rgba(29, 66, 87, .045);
    }
    .chart-title {
        margin: .15rem 0 0 .2rem;
        color: #28465b;
        font-size: .9rem;
        font-weight: 700;
    }
    .stExpander {
        border-color: var(--line) !important;
        border-radius: 14px !important;
        background: rgba(255,255,255,.72);
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        overflow: hidden;
    }
    @media (max-width: 760px) {
        .block-container { padding: 1rem 1rem 2rem; }
        .hero { padding: 1.4rem 1.2rem; }
        .demo-pill { position: static; display: inline-block; margin-bottom: .8rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <span class="demo-pill">● &nbsp; LIVE DEMO</span>
      <p class="hero-kicker">Care, with a closer look</p>
      <h1>Post-discharge patient monitor</h1>
      <p class="hero-subtitle">A clear view of recovery trends, signal quality, and follow-up.</p>
    </div>
    <p class="disclaimer">Clinical decision-support demo only. It does not provide a diagnosis or replace professional care.</p>
    """,
    unsafe_allow_html=True,
)

workspace = st.sidebar.radio(
    "Workspace",
    ["Patient monitor", "Doctor login"],
    key="workspace",
)

if workspace == "Doctor login":
    if not st.session_state.get("doctor_authenticated", False):
        st.markdown(
            """
            <div class="login-card">
              <p class="hero-kicker" style="color:#087f8c">DOCTOR ACCESS</p>
              <h2 style="margin:0">Sign in to the alert inbox</h2>
              <p style="color:#64788a">Review and acknowledge alerts generated by the patient monitor.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        expected_username = os.environ.get("MINEARENA_DEMO_DOCTOR_USERNAME", "doctor")
        expected_password = os.environ.get("MINEARENA_DEMO_DOCTOR_PASSWORD", "demo1234")
        if ("MINEARENA_DEMO_DOCTOR_USERNAME" not in os.environ
                and "MINEARENA_DEMO_DOCTOR_PASSWORD" not in os.environ):
            st.info("Local demo sign-in: username `doctor` · password `demo1234`")
        else:
            st.info("Use the demo doctor credentials configured for this installation.")
        st.warning(
            "Demo access only—not secure authentication. Do not enter real patient information."
        )
        with st.form("doctor_login"):
            username = st.text_input("Doctor username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in")
        if submitted:
            valid_username = hmac.compare_digest(
                username.encode("utf-8"), expected_username.encode("utf-8")
            )
            valid_password = hmac.compare_digest(
                password.encode("utf-8"), expected_password.encode("utf-8")
            )
            if valid_username and valid_password:
                st.session_state.doctor_authenticated = True
                st.session_state.doctor_name = username
                st.rerun()
            else:
                st.error("Sign-in failed. Check the demo credentials and try again.")
        st.stop()

    st.sidebar.markdown(
        f"✅ **Signed in as {escape(st.session_state.get('doctor_name', 'doctor'))}**"
    )
    if st.sidebar.button("Sign out", use_container_width=True):
        st.session_state.doctor_authenticated = False
        st.session_state.pop("doctor_name", None)
        st.rerun()

    st.markdown(
        """
        <div class="section-heading">
          <h2>Doctor alert inbox</h2>
          <span>Shared local demo inbox · refreshes every 5 seconds</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="inbox-note">Alerts from the patient monitor appear here automatically. '
        'Use sample alerts to preview every severity; all sample entries are labeled synthetic.</div>',
        unsafe_allow_html=True,
    )

    @st.fragment(run_every="5s")
    def render_doctor_inbox():
        notifications = list_notifications()
        unread = unread_count()
        latest_id = max((int(item["id"]) for item in notifications), default=0)
        previous_id = st.session_state.get("doctor_last_notification_id")
        if previous_id is None:
            st.session_state.doctor_last_notification_id = latest_id
        elif latest_id > previous_id:
            st.toast("New patient alert received", icon="🔔")
            st.session_state.doctor_last_notification_id = latest_id

        severity_styles = {
            "Urgent": ("tile-urgent", "badge-urgent"),
            "Review": ("tile-review", "badge-review"),
            "Watch": ("tile-watch", "badge-watch"),
            "Sensor issue": ("tile-sensor", "badge-sensor"),
        }
        counts = {
            severity: sum(1 for item in notifications if item["severity"] == severity)
            for severity in severity_styles
        }
        summary_cols = st.columns(4)
        for column, severity in zip(summary_cols, severity_styles):
            tile_class, _ = severity_styles[severity]
            column.markdown(
                f"""
                <div class="severity-tile {tile_class}">
                  <span class="severity-tile-label">{escape(severity)}</span>
                  <span class="severity-tile-count">{counts[severity]}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        unread_col, total_col, action_col = st.columns([1, 1, 2])
        unread_col.metric("Unread", unread)
        total_col.metric("Alerts", len(notifications))
        with action_col:
            st.write("")
            if st.button(
                "✨ Add sample alerts",
                type="primary",
                use_container_width=True,
                key="seed_demo_notifications",
            ):
                added = seed_demo_notifications()
                if added:
                    st.toast(f"Added {added} synthetic demo alerts", icon="✅")
                else:
                    st.toast("Sample alerts are already in the inbox", icon="ℹ️")
                st.rerun(scope="fragment")
            if st.button(
                "Mark all as read",
                disabled=unread == 0,
                use_container_width=True,
                key="mark_all_notifications_read",
            ):
                mark_all_notifications_read()
                st.rerun(scope="fragment")

        if not notifications:
            st.info("No notifications yet. Trigger a patient scenario or add the labeled sample alerts.")
            return

        for item in notifications:
            severity = str(item["severity"])
            alert_class, badge_class = {
                "Urgent": ("alert-urgent", "badge-urgent"),
                "Review": ("alert-review", "badge-review"),
                "Watch": ("alert-watch", "badge-watch"),
                "Sensor issue": ("alert-sensor", "badge-sensor"),
            }[severity]
            notification_id = int(item["id"])
            received_at = datetime.fromisoformat(str(item["created_at"])).astimezone(
                datetime.now().astimezone().tzinfo
            )
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div class="notification-card">
                      <span class="notification-badge {badge_class}">{escape(severity)}</span>
                      <div class="alert-card {alert_class}">
                        <div>
                          <p class="alert-title">{escape(str(item["patient_name"]))} · {escape(str(item["patient_id"]))}</p>
                          <p class="alert-copy">{escape(str(item["message"]))}</p>
                          <p class="alert-action">Suggested next step: {escape(str(item["recommended_action"]))}</p>
                          <p class="notification-meta">Rule: {escape(str(item["rule_id"]))} · Received: {received_at.strftime("%Y-%m-%d %H:%M:%S %Z")}</p>
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if item["read_at"] is None:
                    if st.button(
                        "Acknowledge alert",
                        key=f"acknowledge_notification_{notification_id}",
                    ):
                        mark_notification_read(notification_id)
                        st.rerun(scope="fragment")
                else:
                    acknowledged_at = datetime.fromisoformat(str(item["read_at"])).astimezone(
                        datetime.now().astimezone().tzinfo
                    )
                    st.caption(
                        f"Acknowledged · {acknowledged_at.strftime('%Y-%m-%d %H:%M:%S %Z')}"
                    )

    render_doctor_inbox()
    st.stop()

if "vitals" not in st.session_state:
    st.session_state.vitals = {
        pid: generate_initial_data(patient["base_spo2"]) for pid, patient in PATIENTS.items()
    }
if "checkins" not in st.session_state:
    st.session_state.checkins = []

st.sidebar.markdown("### 🩺  Care console")
st.sidebar.caption("Choose a patient, then explore a demo scenario.")
pid = st.sidebar.selectbox(
    "Select patient",
    list(PATIENTS),
    format_func=lambda patient_id: f"{patient_id} — {PATIENTS[patient_id]['name']}",
)
patient = PATIENTS[pid]
st.sidebar.markdown("### Scenario controls")
if st.sidebar.button("📉  Gradual deterioration", use_container_width=True):
    st.session_state.vitals[pid] = apply_gradual_deterioration(st.session_state.vitals[pid])
if st.sidebar.button("⚡  Sudden spike", use_container_width=True):
    st.session_state.vitals[pid] = apply_sudden_spike(st.session_state.vitals[pid])
if st.sidebar.button("🔌  Probe removal", use_container_width=True):
    st.session_state.vitals[pid] = apply_probe_removal(st.session_state.vitals[pid])
if st.sidebar.button("↺  Reset patient", use_container_width=True):
    st.session_state.vitals[pid] = generate_initial_data(patient["base_spo2"])
st.sidebar.markdown("---")
st.sidebar.caption("Demo data only · Not for clinical use")

df = st.session_state.vitals[pid]
result = evaluate(df, patient)

if result["level"] != "None":
    create_notification(
        patient_id=pid,
        patient_name=patient["name"],
        severity=result["level"],
        message=result["message"],
        recommended_action=result["recommended_action"],
        rule_id=result["rule_id"],
        reading_time=pd.Timestamp(df.iloc[-1]["timestamp"]).isoformat(),
    )
    mobile_api_url = os.environ.get("MINEARENA_MOBILE_API_URL", "").rstrip("/")
    ingest_token = os.environ.get("MINEARENA_ALERT_INGEST_TOKEN", "")
    if not mobile_api_url or not ingest_token:
        st.error(
            "This alert is in the local doctor inbox, but phone push is not configured. "
            "Set MINEARENA_MOBILE_API_URL and MINEARENA_ALERT_INGEST_TOKEN."
        )
    else:
        try:
            push_response = requests.post(
                f"{mobile_api_url}/api/mobile/alerts",
                headers={"X-Alert-Ingest-Token": ingest_token},
                json={
                    "patient_id": pid,
                    "patient_name": patient["name"],
                    "severity": result["level"],
                    "message": result["message"],
                    "recommended_action": result["recommended_action"],
                    "rule_id": result["rule_id"],
                    "reading_time": pd.Timestamp(df.iloc[-1]["timestamp"]).isoformat(),
                },
                timeout=8,
            )
        except requests.RequestException as error:
            st.error(f"Phone push request failed: {error}")
        else:
            if push_response.status_code >= 400:
                try:
                    detail = push_response.json().get("detail", push_response.text)
                except ValueError:
                    detail = push_response.text
                st.error(f"Phone push request failed: {detail}")
            elif push_response.json().get("push_status") == "no_subscribers":
                st.warning(
                    "Alert saved to the mobile inbox, but no doctor phone received a push. "
                    "Open the mobile inbox and enable phone alerts."
                )

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

st.markdown(
    '<div class="section-heading"><h2>Patient overview</h2><span>Recovery snapshot · last reading</span></div>',
    unsafe_allow_html=True,
)
profile_col, metric_cols = st.columns([1.25, 2.3])
with profile_col:
    conditions = "".join(
        f'<span class="tag">{escape(condition)}</span>' for condition in patient["conditions"]
    )
    medications = "".join(
        f'<span class="tag">{escape(medication)}</span>' for medication in patient["medications"]
    )
    st.markdown(
        f"""
        <div class="profile-card">
          <div class="profile-top">
            <div class="avatar">{escape(patient["name"][:1])}</div>
            <div>
              <p class="profile-name">{escape(patient["name"])}</p>
              <p class="profile-meta">{escape(pid)} &nbsp;·&nbsp; {patient["age"]} years &nbsp;·&nbsp; {escape(patient["sex"])}</p>
            </div>
          </div>
          <p class="profile-label">Conditions</p>{conditions}
          <p class="profile-label">Medications</p>{medications}
        </div>
        """,
        unsafe_allow_html=True,
    )

with metric_cols:
    score_col, level_col, spo2_col, signal_col = st.columns(4)
    score_col.metric("Partial NEWS2-style score", "n/a" if result["score"] is None else result["score"])
    level_col.metric("Alert level", result["level"])
    spo2_col.metric("Latest SpO₂", f'{df.iloc[-1]["spo2"]:.1f}%')
    signal_col.metric("Signal quality", result["artifact_status"])
    st.caption("Partial score uses HR, SpO₂, respiratory rate, and temperature. BP and consciousness are unavailable.")

st.markdown(
    '<div class="section-heading"><h2>Latest update</h2><span>Signal interpreted with patient context</span></div>',
    unsafe_allow_html=True,
)
alert_styles = {
    "None": ("alert-none", "✓", "All clear"),
    "Watch": ("alert-watch", "◉", "Keep an eye on trends"),
    "Review": ("alert-review", "!", "Clinical review suggested"),
    "Urgent": ("alert-urgent", "!", "Urgent clinical review"),
    "Sensor issue": ("alert-sensor", "⌁", "Check the sensor"),
}
alert_class, alert_icon, alert_title = alert_styles[result["level"]]
alert_text = (
    "No active clinical alert."
    if result["level"] == "None"
    else result["message"]
)
st.markdown(
    f"""
    <div class="alert-card {alert_class}">
      <div class="alert-icon">{alert_icon}</div>
      <div>
        <p class="alert-title">{alert_title}</p>
        <p class="alert-copy">{escape(alert_text)}</p>
        <p class="alert-action">Suggested next step: {escape(result["recommended_action"])}</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander(
    "How was this interpreted?",
    on_change="rerun",
    key="interpretation_expander",
) as interpretation_expander:
    if interpretation_expander.open:
        st.markdown(f"**Reading:** `{result['trigger_reading']}`")
        st.markdown(f"**Rule applied:** `{result['rule_id']}`")
        st.markdown(f"**Patient profile:** {result['patient_factor']}")
        st.markdown(f"**Trend:** {result['trend']}")
        st.markdown(f"**Data quality:** {result['artifact_status']}")


def vital_chart(data, field, title, unit, color):
    chart_data = data[["timestamp", field]].copy()
    chart_data["timestamp"] = pd.to_datetime(chart_data["timestamp"])
    minimum = float(chart_data[field].min())
    maximum = float(chart_data[field].max())
    padding = max((maximum - minimum) * 0.18, {
        "heart_rate": 2.0,
        "spo2": 1.0,
        "respiratory_rate": 1.0,
        "temperature": 0.2,
    }[field])
    chart_data["chart_floor"] = minimum - padding
    base = alt.Chart(chart_data).encode(
        x=alt.X(
            "timestamp:T",
            axis=alt.Axis(title=None, format="%H:%M", labelAngle=0, grid=False, tickCount=5),
        ),
        y=alt.Y(
            f"{field}:Q",
            axis=alt.Axis(title=None, grid=True, tickCount=4),
            scale=alt.Scale(domain=[minimum - padding, maximum + padding], zero=False, nice=False),
        ),
        tooltip=[
            alt.Tooltip("timestamp:T", title="Time", format="%H:%M:%S"),
            alt.Tooltip(f"{field}:Q", title=f"{title} ({unit})", format=".1f"),
        ],
    )
    area = base.mark_area(color=color, opacity=0.12, interpolate="monotone").encode(
        y2=alt.Y2("chart_floor:Q")
    )
    line = base.mark_line(
        color=color,
        strokeWidth=2.7,
        interpolate="monotone",
        point=alt.OverlayMarkDef(size=20, opacity=0.55),
    )
    return (
        (area + line)
        .properties(height=205)
        .configure_view(stroke=None)
        .configure_axis(
            labelColor="#75899a",
            labelFontSize=10,
            domainColor="#dce6ec",
            gridColor="#edf2f5",
            tickColor="#dce6ec",
        )
    )


chart_specs = [
    ("heart_rate", "Heart rate", "bpm", "#ef6c67"),
    ("spo2", "Blood oxygen", "%", "#168f9b"),
    ("respiratory_rate", "Respiratory rate", "breaths/min", "#8067d8"),
    ("temperature", "Temperature", "°C", "#e7a43c"),
]
with st.expander(
    "Vital signs",
    expanded=False,
    on_change="rerun",
    key="vital_signs_expander",
) as vital_signs_expander:
    if vital_signs_expander.open:
        st.markdown(
            '<div class="section-heading"><h2>Vital signs</h2><span>Hover over a line to inspect a reading</span></div>',
            unsafe_allow_html=True,
        )
        for row_start in (0, 2):
            chart_cols = st.columns(2)
            for column, (field, title, unit, color) in zip(
                chart_cols, chart_specs[row_start:row_start + 2]
            ):
                with column:
                    with st.container(border=True):
                        st.markdown(
                            f'<p class="chart-title">{title} <span style="font-weight:400;color:#8193a1">· {unit}</span></p>',
                            unsafe_allow_html=True,
                        )
                        st.altair_chart(
                            vital_chart(df, field, title, unit, color),
                            width="stretch",
                        )

st.markdown(
    '<div class="section-heading"><h2>Alert history</h2><span>Patient-specific alerts saved to the shared inbox</span></div>',
    unsafe_allow_html=True,
)
saved_alerts = [
    item for item in list_notifications()
    if item["patient_id"] == pid
]
if saved_alerts:
    history = pd.DataFrame([
        {
            "time": datetime.fromisoformat(str(item["created_at"]))
            .astimezone(datetime.now().astimezone().tzinfo)
            .strftime("%H:%M:%S"),
            "patient": f"{item['patient_id']} {item['patient_name']}",
            "level": item["severity"],
            "rule": item["rule_id"],
            "reason": item["message"],
        }
        for item in saved_alerts
    ])
elif st.session_state.alert_log:
    history = pd.DataFrame(st.session_state.alert_log[::-1])
else:
    history = None

if history is not None:
    severity_colors = {
        "Urgent": ("#fff0f0", "#852d34"),
        "Review": ("#fff0e4", "#814315"),
        "Watch": ("#fff7df", "#755413"),
        "Sensor issue": ("#f1efff", "#514384"),
    }

    def color_severity(severity):
        background, foreground = severity_colors.get(severity, ("#f3f7fa", "#355468"))
        return f"background-color: {background}; color: {foreground}; font-weight: 700"

    st.dataframe(
        history.style.map(color_severity, subset=["level"]),
        hide_index=True,
        use_container_width=True,
    )
else:
    st.caption("No alerts yet. Try a scenario from the care console or load sample alerts in the doctor inbox.")

with st.expander(
    "Patient symptom check-in",
    on_change="rerun",
    key="symptom_checkin_expander",
) as symptom_checkin_expander:
    if symptom_checkin_expander.open:
        with st.form("checkin"):
            sx_cols = st.columns(5)
            symptom_names = ["Breathlessness", "Fever", "Dizziness", "Chest pain", "Reduced activity"]
            sx = {
                name: column.slider(name, 0, 10, 0)
                for name, column in zip(symptom_names, sx_cols)
            }
            if st.form_submit_button("Save check-in"):
                st.session_state.checkins.append({"patient": pid, **sx})
                st.success("Saved locally. It will be sent to the backend once the API is ready.")
        if st.session_state.checkins:
            st.dataframe(
                pd.DataFrame(st.session_state.checkins),
                hide_index=True,
                width="stretch",
            )

with st.expander(
    "Performance report · placeholder",
    on_change="rerun",
    key="performance_report_expander",
) as performance_report_expander:
    if performance_report_expander.open:
        st.caption("These metrics will be computed from the team's replay log.")
        st.dataframe(
            pd.DataFrame({
                "Metric": ["Detection lead time", "Alerts per patient-day", "False alerts", "Artifact alerts suppressed"],
                "Our monitor": ["—", "—", "—", "—"],
                "Fixed threshold": ["—", "—", "—", "—"],
            }),
            hide_index=True,
            width="stretch",
        )
