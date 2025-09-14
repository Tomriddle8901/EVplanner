from fastapi import FastAPI, HTTPException
import requests
import math
import polyline  # pip install polyline

# ========== CONFIG ==========
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImRiMjMwZWRlNTFjZDRmZTM5ODE2YjIxOWE2MDg5ZTBjIiwiaCI6Im11cm11cjY0In0="
ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

app = FastAPI(
    title="Route Service",
    description="Fetch driving distance, duration, and route coordinates",
    version="1.0.0"
)

# ========== HELPERS ==========

def geocode_address(address: str):
    """Convert address string into (lat, lon) coordinates"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    response = requests.get(url, params=params, headers={"User-Agent": "EVPlanner/1.0"})
    data = response.json()
    if len(data) > 0:
        return float(data[0]["lat"]), float(data[0]["lon"])
    raise HTTPException(status_code=404, detail=f"Address not found: {address}")

def haversine(coord1, coord2):
    """Compute distance between two lat/lon points in km"""
    R = 6371
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def sample_route(coords, step_km=50):
    """Sample route points every ~step_km km along the path"""
    sampled = [coords[0]]
    dist_acc = 0
    for i in range(1, len(coords)):
        dist = haversine(coords[i - 1], coords[i])
        dist_acc += dist
        if dist_acc >= step_km:
            sampled.append(coords[i])
            dist_acc = 0
    sampled.append(coords[-1])
    return sampled

# ========== ENDPOINTS ==========

@app.get("/route")
def get_route(start: str, end: str):
    """Return distance, duration, and sampled coordinates along a route"""
    try:
        # Geocode addresses
        start_coords = geocode_address(start)
        end_coords = geocode_address(end)

        headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
        body = {
            "coordinates": [[start_coords[1], start_coords[0]], [end_coords[1], end_coords[0]]]
        }

        # Request route
        response = requests.post(ORS_URL, json=body, headers=headers)
        data = response.json()

        # ✅ Handle ORS error properly
        if "routes" not in data:
            raise HTTPException(status_code=400, detail=f"ORS Error: {data.get('error', data)}")

        route = data["routes"][0]

        # Extract distance + duration
        distance_km = route["summary"]["distance"] / 1000
        duration_min = route["summary"]["duration"] / 60

        # Extract geometry
        geometry = route["geometry"]
        coords = polyline.decode(geometry)  # always returns [(lat, lon), ...]

        # Sample route points
        sampled_points = sample_route(coords, step_km=50)

        return {
            "distance_km": round(distance_km, 2),
            "duration_min": round(duration_min, 2),
            "start_coords": start_coords,
            "end_coords": end_coords,
            "route_points": coords,        # full path
            "sampled_points": sampled_points
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route service error: {str(e)}")
