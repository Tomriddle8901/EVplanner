import pandas as pd

# Load raw dataset
file_path = "C:/Users/hp_pa/Desktop/EV APP/archive (2)/electric_vehicles_spec_2025.csv"
df = pd.read_csv(file_path)

# Keep only relevant columns
df = df[["brand", "model", "battery_capacity_kWh", "efficiency_wh_per_km", "range_km"]]

# Drop rows with missing values in these key columns
df = df.dropna(subset=["brand", "model", "battery_capacity_kWh", "efficiency_wh_per_km", "range_km"])

# Remove duplicates
df = df.drop_duplicates()

# Clean text fields
df["brand"] = df["brand"].str.strip().str.title()   # e.g., 'tesla' -> 'Tesla'
df["model"] = df["model"].str.strip().str.title()

# Create easy-to-use car name
df["car_name"] = df["brand"] + " " + df["model"]

# Reset index
df = df.reset_index(drop=True)

# Export cleaned CSV
cleaned_csv_path = "C:/Users/hp_pa/Desktop/EV APP/archive (2)/cleaned_electric_vehicles.csv"
df.to_csv(cleaned_csv_path, index=False)

# Export JSON (dictionary format for project use)
car_dict = df.set_index("car_name")[["battery_capacity_kWh", "efficiency_wh_per_km", "range_km"]].to_dict(orient="index")
cleaned_json_path = "C:/Users/hp_pa/Desktop/EV APP/archive (2)/cleaned_electric_vehicles.json"
pd.Series(car_dict).to_json(cleaned_json_path, indent=4)

print("✅ Dataset cleaned and saved!")
print(f"CSV saved at: {cleaned_csv_path}")
print(f"JSON saved at: {cleaned_json_path}")
print("\nExample dictionary entry:")
print(list(car_dict.items())[:3])  # Show first 3 cars
