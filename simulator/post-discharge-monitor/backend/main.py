from fastapi import FastAPI
from api.observations import router as observation_router
from api.patients import router as patient_router

# 1. Define the FastAPI application instance first
app = FastAPI(title="Post-Discharge Deterioration Monitor API")

# 2. Register your routers after 'app' is created
app.include_router(observation_router)
app.include_router(patient_router)

# 3. Add your health check endpoint
@app.get("/health")
def health():
    return {"status": "healthy"}