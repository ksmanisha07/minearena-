from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.alerts import router as alert_router
from api.mobile import router as mobile_router
from api.observations import router as observation_router
from api.patients import router as patient_router

# 1. Define the FastAPI application instance first
app = FastAPI(title="Post-Discharge Deterioration Monitor API")

# 2. Register your routers after 'app' is created
app.include_router(observation_router)
app.include_router(patient_router)
app.include_router(alert_router)
app.include_router(mobile_router)

# 3. Add your health check endpoint
@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/mobile", include_in_schema=False)
def mobile_app_redirect():
    return RedirectResponse("/mobile/")


app.mount(
    "/mobile",
    StaticFiles(directory=Path(__file__).parent / "static" / "mobile", html=True),
    name="mobile",
)