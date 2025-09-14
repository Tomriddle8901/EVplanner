from fastapi import FastAPI, HTTPException
import requests

OPENCHARGE_URL = "https://api.openchargemap.io/v3/poi"
OPENCHARGE_KEY = "05b614e7-d737-49af-af71-d801e6638693"

app = FastAPI(
    title="Charging Service",
    description="Fetch EV charging stations",
    version="1.0.0"
)

def get_charging_stations(lat, lon, distance_km=10):
    params = {
        "key": OPENCHARGE_KEY,
        "latitude": lat,
        "longitude": lon,
        "distance": distance_km,
        "distanceunit": "KM",
        "maxresults": 5
    }
    response = requests.get(OPENCHARGE_URL, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=response.text)
    data = response.json()
    stations = []
    for s in data:
        stations.append({
            "name": s.get("AddressInfo", {}).get("Title"),
            "lat": s.get("AddressInfo", {}).get("Latitude"),
            "lon": s.get("AddressInfo", {}).get("Longitude"),
            "power_kW": s.get("Connections", [{}])[0].get("PowerKW", "N/A"),
            "address": s.get("AddressInfo", {}).get("AddressLine1")
        })
    return stations

@app.get("/charging")
def charging(lat: float, lon: float):
    try:
        return {"charging_stations": get_charging_stations(lat, lon)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
