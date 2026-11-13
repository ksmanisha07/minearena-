# Deterotion Monitor

A demo application for monitoring patients after hospital discharge. It tracks vital signs and symptom check-ins, flags potential health deterioration, and sends alerts to a doctor’s mobile inbox. Uses simulated data and is not intended for clinical use.

<img width="1496" height="728" alt="image" src="https://github.com/user-attachments/assets/77edbd54-c153-4487-a4af-e5b4c6b438f5" />


## Features

- personalized health Monitoring 
- Early Deterioration  Detection 
- Smart Alert And False Alert Detection 

## Tech Stack
Languages: Python, HTML, CSS, JavaScript
Frameworks: Streamlit (patient dashboard), FastAPI (doctor alert API)
Database: SQLite
Notifications: Web Push with a service worker (PWA)

## Getting Started

### Requirements
- Python 3.10 or later

### Install dependencies

From the project root, create a virtual environment and install the dashboard and API dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r dashboard\requirements.txt
python -m pip install -r post-discharge-monitor\backend\requirements.txt
Open two PowerShell terminals in the project root and activate the virtual environment in each.

In Terminal 1, configure the local demo tokens and start the mobile alert API:
cd post-discharge-monitor\backend
$env:MINEARENA_DOCTOR_ACCESS_TOKEN = "your-doctor-demo-token"
$env:MINEARENA_ALERT_INGEST_TOKEN = "your-alert-demo-token"
python -m uvicorn main:app --host 127.0.0.1 --port 8000
cd post-discharge-monitor\backend
$env:MINEARENA_DOCTOR_ACCESS_TOKEN = "your-doctor-demo-token"
$env:MINEARENA_ALERT_INGEST_TOKEN = "your-alert-demo-token"
python -m uvicorn main:app --host 127.0.0.1 --port 8000
cd dashboard
$env:MINEARENA_MOBILE_API_URL = "http://127.0.0.1:8000"
$env:MINEARENA_ALERT_INGEST_TOKEN = "your-alert-demo-token"
python -m streamlit run app.py --server.port 8501

