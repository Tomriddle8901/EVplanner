from fastapi import FastAPI, HTTPException
import requests
import os

# Config: service URLs (Docker networking uses container names, not localhost)
VEHICLE_SERVICE_URL = os.getenv("VEHICLE_SERVICE_URL", "http://vehicle-service:8000/vehicle")
ROUTE_SERVICE_URL = os.getenv("ROUTE_SERVICE_URL", "http://route-service:8001/route")
CHARGING_SERVICE_URL = os.getenv("CHARGING_SERVICE_URL", "http://charging-service:8003/charging")

BUFFER_KM = 10  # always stop before this safety buffer

app = FastAPI(
    title="Prediction Service",
    description="Checks trip feasibility and suggests charging stops",
    version="2.0.0"
)

# ---------- HELPERS ----------

def get_vehicle_data(car_name: str):
    url = f"{VEHICLE_SERVICE_URL}/{car_name}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail=response.json())

def get_route_data(start: str, end: str):
    url = f"{ROUTE_SERVICE_URL}?start={start}&end={end}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail=response.json())

def get_charging_stations(lat: float, lon: float):
    url = f"{CHARGING_SERVICE_URL}?lat={lat}&lon={lon}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("charging_stations", [])
    return []

# ---------- ENDPOINT ----------

@app.get("/predict")
def predict_trip(car_name: str, battery_percent: float, start: str, end: str):
    try:
        # 1. Get vehicle info
        car = get_vehicle_data(car_name)
        full_range = car["range_km"]
        available_range = full_range * (battery_percent / 100.0)

        # 2. Get route info
        route = get_route_data(start, end)
        distance_km = route["distance_km"]
        sampled_points = route.get("sampled_points", [])

        # 3. Plan stops
        recommended_stops = []
        traveled = 0
        current_range = available_range

        for i in range(1, len(sampled_points)):
            leg_distance = route["distance_km"] / (len(sampled_points) - 1)  # approx per leg
            traveled += leg_distance
            current_range -= leg_distance

            if current_range <= BUFFER_KM:  # need to stop
                lat, lon = sampled_points[i]
                stations = get_charging_stations(lat, lon)

                if stations:
                    best_station = sorted(stations, key=lambda s: -s.get("power_kW", 0))[0]
                    recommended_stops.append(best_station)
                    current_range = full_range  # reset after charging

        return {
            "car": car_name,
            "battery_percent": battery_percent,
            "available_range_km": round(available_range, 2),
            "trip_distance_km": round(distance_km, 2),
            "recommended_stops": recommended_stops
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
