import requests, json
BASE = "http://localhost:5000"
resp = requests.post(f"{BASE}/api/auth/login", json={"email": "admin@demo.com", "password": "demo123"})
token = resp.json()["token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

for sc_name in ["3_rider_corridor", "5_rider_spread", "7_rider_max"]:
    sc = requests.post(f"{BASE}/api/demo/load", json={"scenario": sc_name}, headers=headers).json()
    r = requests.post(f"{BASE}/api/analytics/compare", json={"driver_start": sc["driver_start"], "riders": sc["riders"], "vehicle_capacity": 4}, headers=headers).json()
    print(f"\n=== {sc_name} ===")
    for k,name in [("dp","DP"),("nearest_neighbor","NN"),("cheapest_insertion","CI")]:
        a = r[k]
        stops = [f'{s["label"]}' for s in a["route"]]
        print(f"  {name}: {a['total_distance_km']}km | Route: {' > '.join(stops)}")
