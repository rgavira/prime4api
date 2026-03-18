from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

with open('examples/mailersend.yaml', 'r') as f:
    yaml_text = f.read()

print("--- Test 1: Iterative Evaluation (No Endpoint Specified) ---")
req = {
    "datasheet_source": yaml_text,
    "plan_name": "free",
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
    "alias": "under_review_reputation",
    "operation": "min_time",
    "operation_params": {"capacity_goal": 10}
}
res2 = client.post("/api/v1/datasheet/evaluate", json=req2)
print(f"Status Code: {res2.status_code}")
if res2.status_code == 200:
    print(json.dumps(res2.json(), indent=2))
else:
    print(res2.text)


# =============================================================================
# Tests T1: Acumulación jerárquica de límites
#
# Plan 'free' tiene:
#   - quota global del plan: quota_100_req_day (100 requests/día)
# Endpoint v1/email / alias healthy_reputation tiene:
#   - rate: rate_120_min (120 req/min)
#   - quota: quota_500_emails_month (500 emails/mes)
#
# Con acumulación correcta, BoundedRate recibe AMBAS quotas:
#   [Rate(120,1min), Quota(100,1day), Quota(500,1month)]
# La quota del plan (100/día) ES la más restrictiva y se convierte en el
# cuello de botella real: después de 100 requests, hay que esperar 1 día.
#
# Comportamiento ESPERADO con acumulación:
#   - quota_exhaustion_threshold devuelve 2 entradas (100/day y 500/month)
#   - min_time(150) ≈ 1 día (la quota 100/day obliga a esperar un día completo)
#
# Comportamiento INCORRECTO sin acumulación (fallback OR):
#   - quota_exhaustion_threshold devuelve 1 entrada (sólo 500/month)
#   - min_time(150) ≈ 1 min (ignora la quota del plan)
# =============================================================================

print("\n--- Test T1-A: Acumulación jerárquica - quota_exhaustion_threshold ---")
print("Plan 'free', endpoint v1/email, alias healthy_reputation")
print("Límites esperados en BoundedRate: Rate(120/min) + Quota(100/día) + Quota(500/mes)")
print("-> quota_exhaustion_threshold debe devolver 2 entradas (una por cada quota activa)")
req_t1a = {
    "datasheet_source": yaml_text,
    "plan_name": "free",
    "endpoint_path": "v1/email",
    "alias": "under_review_reputation",
    "operation": "quota_exhaustion_threshold",
    "operation_params": {}
}
res_t1a = client.post("/api/v1/datasheet/evaluate", json=req_t1a)
print(f"Status Code: {res_t1a.status_code}")
if res_t1a.status_code == 200:
    data_t1a = res_t1a.json()
    print(json.dumps(data_t1a, indent=2))
    thresholds = data_t1a["results"][0]["result"]
    assert len(thresholds) == 2, (
        f"FAIL: Se esperaban 2 entradas en quota_exhaustion_threshold "
        f"[Quota(100/día plan), Quota(500/mes alias)], "
        f"pero se obtuvieron {len(thresholds)}. "
        f"Posiblemente la quota global del plan no se está acumulando."
    )
    print(f"PASS: quota_exhaustion_threshold devuelve {len(thresholds)} entradas — acumulación plan→alias correcta.")
else:
    print(res_t1a.text)
    assert False, "Request failed"


print("\n--- Test T1-B: Acumulación jerárquica - min_time refleja quota del plan ---")
print("Plan 'free', endpoint v1/email, alias healthy_reputation, capacity_goal=150")
print("Con quota 100/día del plan activa: min_time(150) debe ser ~1 día")
print("Sin acumulación (bug): min_time(150) sería ~1 min (sólo Rate 120/min)")
req_t1b = {
    "datasheet_source": yaml_text,
    "plan_name": "free",
    "endpoint_path": "v1/email",
    "alias": "healthy_reputation",
    "operation": "min_time",
    "operation_params": {"capacity_goal": 150}
}
res_t1b = client.post("/api/v1/datasheet/evaluate", json=req_t1b)
print(f"Status Code: {res_t1b.status_code}")
if res_t1b.status_code == 200:
    data_t1b = res_t1b.json()
    print(json.dumps(data_t1b, indent=2))
    result_time = data_t1b["results"][0]["result"]
    assert "day" in result_time, (
        f"FAIL: Se esperaba un resultado en días (~1 day) para min_time(150) "
        f"con la quota del plan de 100 req/día activa, "
        f"pero se obtuvo: '{result_time}'. "
        f"La quota global del plan no está siendo acumulada."
    )
    print(f"PASS: min_time(150) = '{result_time}' refleja correctamente la quota 100/día del plan.")
else:
    print(res_t1b.text)
    assert False, "Request failed"


print("\n--- Test T1-C: Quota del plan inalcanzable es descartada por BoundedRate ---")
print("Plan 'starter', endpoint v1/email, alias under_review_reputation")
print("starter tiene quota_100k_req_day (100K/día) pero Rate es 10/min → max 14400/día < 100K")
print("-> BoundedRate recibe [Rate(10/min), Quota(100K/día), Quota(50K/mes)]")
print("-> Quota 100K/día excede capacidad del rate → descartada por BoundedRate")
print("-> quota_exhaustion_threshold debe devolver 1 entrada: sólo Quota(50K/mes)")
req_t1c = {
    "datasheet_source": yaml_text,
    "plan_name": "starter",
    "endpoint_path": "v1/email",
    "alias": "under_review_reputation",
    "operation": "quota_exhaustion_threshold",
    "operation_params": {}
}
res_t1c = client.post("/api/v1/datasheet/evaluate", json=req_t1c)
print(f"Status Code: {res_t1c.status_code}")
if res_t1c.status_code == 200:
    data_t1c = res_t1c.json()
    print(json.dumps(data_t1c, indent=2))
    thresholds_c = data_t1c["results"][0]["result"]
    assert len(thresholds_c) == 1, (
        f"FAIL: Se esperaba 1 entrada en quota_exhaustion_threshold [Quota(50K/mes)]. "
        f"La quota 100K/día del plan es inalcanzable con Rate 10/min (14400/día máx) "
        f"y BoundedRate debe descartarla. Se obtuvieron {len(thresholds_c)}."
    )
    print(f"PASS: quota_exhaustion_threshold devuelve {len(thresholds_c)} entrada — quota inalcanzable descartada.")
else:
    print(res_t1c.text)
    assert False, "Request failed"
