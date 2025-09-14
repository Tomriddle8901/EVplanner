import pandas as pd
import requests

# ========== CONFIG ==========
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImRiMjMwZWRlNTFjZDRmZTM5ODE2YjIxOWE2MDg5ZTBjIiwiaCI6Im11cm11cjY0In0="
ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

# ========== LOAD CAR DATA ==========
df = pd.read_csv("C:/Users/hp_pa/Desktop/EV APP/archive (2)/cleaned_electric_vehicles.csv")
car_dict = df.set_index("car_name")[["battery_capacity_kWh", "efficiency_wh_per_km", "range_km"]].to_dict(orient="index")

# ========== FUNCTIONS ==========
def geocode_address(address, country_code="ca"):
    """Convert address into lat/lon using OpenStreetMap Nominatim with country bias."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1, "countrycodes": country_code}
    response = requests.get(url, params=params, headers={"User-Agent": "EVPlanner/1.0"})
    data = response.json()
    if len(data) > 0:
        return float(data[0]["lat"]), float(data[0]["lon"])
    else:
        raise Exception(f"Address not found: {address}")

def get_distance_km(start, end):
    """Get driving distance between two lat/lon coordinates using OpenRouteService."""
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    body = {"coordinates": [[start[1], start[0]], [end[1], end[0]]]}  # lon, lat order
    response = requests.post(ORS_URL, json=body, headers=headers)
    data = response.json()
    if "routes" in data:
        return data["routes"][0]["summary"]["distance"] / 1000  # meters → km
    else:
        raise Exception("ORS Error: " + str(data))

def calculate_available_range(car_name, battery_percent):
    """Calculate available range for car at given battery %."""
    car = car_dict.get(car_name)
    if not car:
        raise ValueError("Car not found in dataset!")
    full_range = car["range_km"]
    return full_range * (battery_percent / 100.0)

# ========== MAIN ==========
def main():
    print("⚡ EV Route Planner ⚡")

    start_address = input("\nEnter starting location: ")
    end_address = input("Enter destination: ")
    car_name = input("Enter your car model (must match dataset): ")
    battery_percent = float(input("Enter current battery percentage (0-100): "))

    try:
        start_coords = geocode_address(start_address)
        end_coords = geocode_address(end_address)
        distance_km = get_distance_km(start_coords, end_coords)
        available_range = calculate_available_range(car_name, battery_percent)

        print("\n===== Trip Summary =====")
        print(f"Car: {car_name}")
        print(f"Route: {start_address} → {end_address}")
        print(f"Distance: {distance_km:.2f} km")
        print(f"Available Range: {available_range:.2f} km (Battery: {battery_percent}%)")

        if available_range >= distance_km:
            print("✅ Trip is possible without charging!")
        else:
            print("⚠️ Trip is NOT possible with current battery. You’ll need to recharge.")

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
