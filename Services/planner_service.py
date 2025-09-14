from fastapi import FastAPI, HTTPException
import requests
import os
from fastapi.middleware.cors import CORSMiddleware

# ===== Service URLs =====
PREDICTION_SERVICE_URL = os.getenv("PREDICTION_SERVICE_URL", "http://prediction-service:8002/predict")
ROUTE_SERVICE_URL = os.getenv("ROUTE_SERVICE_URL", "http://route-service:8001/route")

app = FastAPI(
    title="Planner Service",
    description="Final orchestrator that provides clean EV trip plans",
    version="1.0.0"
)

# ===== Enable CORS (for frontend access) =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow all origins in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Helpers =====
def call_prediction_service(car_name: str, battery_percent: float, start: str, end: str):
    params = {"car_name": car_name, "battery_percent": battery_percent, "start": start, "end": end}
    r = requests.get(PREDICTION_SERVICE_URL, params=params)
    if r.status_code == 200:
        return r.json()
    raise HTTPException(status_code=r.status_code, detail=r.text)

def call_route_service(start: str, end: str):
    params = {"start": start, "end": end}
    r = requests.get(ROUTE_SERVICE_URL, params=params)
    if r.status_code == 200:
        return r.json()
    raise HTTPException(status_code=r.status_code, detail=r.text)

# ===== Endpoint =====
@app.get("/plan")
def get_plan(car_name: str, battery_percent: float, start: str, end: str):
    """
    Orchestrates trip plan:
    - Gets route & distance
    - Adjusts range
    - Picks charging stops
    """
    try:
        pred_data = call_prediction_service(car_name, battery_percent, start, end)
        route_data = call_route_service(start, end)

        trip_summary = {
            "car": car_name,
            "start": start,
            "end": end,
            "trip_distance_km": round(pred_data["trip_distance_km"], 2)
        }

        return {
            "trip_summary": trip_summary,
            "stops": pred_data.get("recommended_stops", []),
            "route_points": route_data.get("route_points", []),  # ✅ now frontend gets route
            "final_arrival": end
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
