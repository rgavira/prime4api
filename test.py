from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

with open('examples/mailersend.yaml', 'r') as f:
    yaml_text = f.read()

print("--- Test 1: Iterative Evaluation (No Endpoint Specified) ---")
req = {
    "datasheet_source": yaml_text,
    "plan_name": "professional",
    "operation": "min_time",
    "operation_params": {"capacity_goal": 28}
}

res = client.post("/api/v1/datasheet/evaluate", json=req)
print(f"Status Code: {res.status_code}")
if res.status_code == 200:
    print(json.dumps(res.json(), indent=2))
else:
    print(res.text)


print("\n--- Test 2: Specific Endpoint and Alias ---")
req2 = {
    "datasheet_source": yaml_text,
    "plan_name": "starter",
    "endpoint_path": "v1/email",
    "reputation_state": "under_review_reputation",
    "operation": "min_time",
    "operation_params": {"capacity_goal": 10}
}
res2 = client.post("/api/v1/datasheet/evaluate", json=req2)
print(f"Status Code: {res2.status_code}")
if res2.status_code == 200:
    print(json.dumps(res2.json(), indent=2))
else:
    print(res2.text)
