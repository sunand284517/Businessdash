"""Simple backend API for health and readiness checks."""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .gemini_service import get_api_key

app = FastAPI(title="BusinessDash Backend")


@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})


@app.get("/ready")
def ready():
    """Check whether required configuration (API key) is present."""
    api_key = get_api_key()
    if api_key:
        return JSONResponse({"ready": True})
    return JSONResponse({"ready": False, "reason": "Missing API key"}, status_code=503)
