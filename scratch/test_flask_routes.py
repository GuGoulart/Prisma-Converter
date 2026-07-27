import sys, os
sys.path.insert(0, os.path.abspath("."))

from app import app

print("Initializing Flask test client...")
client = app.test_client()

# 1. Test GET /ferramentas-avancadas
res = client.get("/ferramentas-avancadas")
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
assert b"Baixar V\xc3\xaddeo / \xc3\x81udio por Link" in res.data or b"Baixar" in res.data, "Form missing from page HTML"
print("GET /ferramentas-avancadas OK")

# 2. Test status endpoint with unknown job_id
res_status = client.get("/api/media/download-status/invalid_job_id")
assert res_status.status_code == 404, f"Expected 404, got {res_status.status_code}"
print("GET /api/media/download-status/<invalid> OK (404 as expected)")

print("ALL FLASK ROUTE CHECKS PASSED PERFECTLY!")
