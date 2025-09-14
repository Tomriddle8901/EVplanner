from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "cleaned_electric_vehicles.csv")

# ✅ Load dataset safely
if not os.path.exists(DATA_PATH):
    raise RuntimeError(f"❌ Dataset not found at {DATA_PATH}")

df = pd.read_csv(DATA_PATH)

# ✅ Build lookup dictionary from CSV
# assumes CSV has column: car_name, battery_capacity_kWh, efficiency_wh_per_km, range_km
car_dict = df.set_index("car_name")[["battery_capacity_kWh", "efficiency_wh_per_km", "range_km"]].to_dict(orient="index")

app = FastAPI(
    title="Vehicle Service",
    description="Fetch EV specifications from dataset",
    version="1.0.0"
)

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # For development, allow everything
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/vehicle/{car_name}")
def get_vehicle(car_name: str):
    car = car_dict.get(car_name)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found in dataset")
    return {"car_name": car_name, **car}

@app.get("/vehicles")
def list_vehicles(limit: int = 10):
    return list(car_dict.keys())[:limit]
