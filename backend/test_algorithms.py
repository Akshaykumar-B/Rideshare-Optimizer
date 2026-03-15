"""Test script to call the comparison API and inspect raw algorithm outputs."""
import requests
import json

BASE = "http://localhost:5000"

# First, login as admin to get a token
login_resp = requests.post(f"{BASE}/api/auth/login", json={"email": "admin@demo.com", "password": "demo123"})
if login_resp.status_code != 200:
    print("Login failed:", login_resp.text)
    exit(1)

token = login_resp.json()["token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Test with 3-rider corridor
print("=" * 60)
print("SCENARIO: 3-Rider Corridor")
print("=" * 60)

scenario_resp = requests.post(f"{BASE}/api/demo/load", json={"scenario": "3_rider_corridor"}, headers=headers)
scenario = scenario_resp.json()

compare_resp = requests.post(f"{BASE}/api/analytics/compare", json={
    "driver_start": scenario["driver_start"],
    "riders": scenario["riders"],
    "vehicle_capacity": 4,
}, headers=headers)

result = compare_resp.json()

for alg_key, alg_name in [("dp", "DP"), ("nearest_neighbor", "Nearest Neighbor"), ("cheapest_insertion", "Cheapest Insertion")]:
    alg = result[alg_key]
    route_order = " -> ".join([f'{s["label"]}({s["type"]})' for s in alg["route"]])
    print(f"\n{alg_name}:")
    print(f"  Distance: {alg['total_distance_km']} km")
    print(f"  Time: {alg['total_time_min']} min")
    print(f"  Route: {route_order}")
    print(f"  Compute: {alg['computation_time_ms']} ms")

# Test with 5-rider spread
print("\n" + "=" * 60)
print("SCENARIO: 5-Rider City-Wide Spread")
print("=" * 60)

scenario_resp = requests.post(f"{BASE}/api/demo/load", json={"scenario": "5_rider_spread"}, headers=headers)
scenario = scenario_resp.json()

compare_resp = requests.post(f"{BASE}/api/analytics/compare", json={
    "driver_start": scenario["driver_start"],
    "riders": scenario["riders"],
    "vehicle_capacity": 4,
}, headers=headers)

result = compare_resp.json()

for alg_key, alg_name in [("dp", "DP"), ("nearest_neighbor", "Nearest Neighbor"), ("cheapest_insertion", "Cheapest Insertion")]:
    alg = result[alg_key]
    route_order = " -> ".join([f'{s["label"]}({s["type"]})' for s in alg["route"]])
    print(f"\n{alg_name}:")
    print(f"  Distance: {alg['total_distance_km']} km")
    print(f"  Time: {alg['total_time_min']} min")
    print(f"  Route: {route_order}")
    print(f"  Compute: {alg['computation_time_ms']} ms")

# Test with 7-rider max
print("\n" + "=" * 60)
print("SCENARIO: 7-Rider Maximum DP")
print("=" * 60)

scenario_resp = requests.post(f"{BASE}/api/demo/load", json={"scenario": "7_rider_max"}, headers=headers)
scenario = scenario_resp.json()

compare_resp = requests.post(f"{BASE}/api/analytics/compare", json={
    "driver_start": scenario["driver_start"],
    "riders": scenario["riders"],
    "vehicle_capacity": 4,
}, headers=headers)

result = compare_resp.json()

for alg_key, alg_name in [("dp", "DP"), ("nearest_neighbor", "Nearest Neighbor"), ("cheapest_insertion", "Cheapest Insertion")]:
    alg = result[alg_key]
    route_order = " -> ".join([f'{s["label"]}({s["type"]})' for s in alg["route"]])
    print(f"\n{alg_name}:")
    print(f"  Distance: {alg['total_distance_km']} km")
    print(f"  Time: {alg['total_time_min']} min")
    print(f"  Route: {route_order}")
    print(f"  Compute: {alg['computation_time_ms']} ms")
