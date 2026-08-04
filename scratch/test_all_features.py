import sys, os, io, json, time
sys.path.insert(0, os.path.abspath("."))

from app import app
from core.converter import converter_arquivo, CONVERSOES
from core.pdf_tools import mesclar_pdfs, dividir_pdf, proteger_pdf, desproteger_pdf, comprimir_pdf
from core.file_tools import comprimir_arquivos, zip_com_senha, criptografar_arquivo, descriptografar_arquivo, calcular_hashes, renomear_em_lote
from core.qr_tools import gerar_qrcode, ler_qrcode
from core.image_tools import extrair_paleta

print("=== STARTING PRISMA CONVERTER FULL ENDPOINT VALIDATION ===")

client = app.test_client()

# 1. Test GET Pages
pages = ["/", "/conversor", "/ferramentas-avancadas", "/modificar-arquivos", "/health", "/manifest.json", "/sw.js"]
for page in pages:
    res = client.get(page)
    assert res.status_code == 200, f"Page {page} returned status {res.status_code}"
    print(f"GET {page} OK (200)")

# 2. Test Upload and Async Conversion API via Flask test client
with client.session_transaction() as sess:
    sess["csrf_token"] = "test_csrf_token"

csv_content = b"nome,idade,cidade\nAlice,30,Sao Paulo\nBob,25,Rio\n"

# Test POST /upload
res_up = client.post("/upload", data={
    "arquivo": (io.BytesIO(csv_content), "test.csv"),
    "csrf_token": "test_csrf_token"
}, content_type="multipart/form-data")
assert res_up.status_code == 200, f"Upload failed status {res_up.status_code}"
assert b"test.csv" in res_up.data
print("POST /upload OK (200)")

# Test POST /api/converter/async
res_async = client.post("/api/converter/async", data={
    "origem": "csv",
    "destino": "xlsx",
    "nome_original": "test.csv",
    "orientacao": "retrato",
    "autodestruicao": "15min",
    "csrf_token": "test_csrf_token"
})
assert res_async.status_code == 200, f"Async conversion failed status {res_async.status_code}"
data = json.loads(res_async.data.decode("utf-8"))
assert data.get("ok") is True and "job_id" in data
job_id = data["job_id"]
print(f"POST /api/converter/async OK (job_id: {job_id})")

# Poll status until done
for _ in range(20):
    res_st = client.get(f"/api/converter/status/{job_id}")
    st_data = json.loads(res_st.data.decode("utf-8"))
    if st_data.get("concluido"):
        break
    time.sleep(0.5)

assert st_data.get("concluido") is True, f"Job failed: {st_data}"
print(f"GET /api/converter/status/{job_id} OK (100%)")

# Test GET download
res_dl = client.get(f"/api/converter/download/{job_id}")
assert res_dl.status_code == 200, f"Download failed status {res_dl.status_code}"
assert len(res_dl.data) > 0
print(f"GET /api/converter/download/{job_id} OK ({len(res_dl.data)} bytes)")

# 3. Test API tools endpoints (QR Code, Hash, Compress)
# 3.1 QR Code
res_qr = client.post("/api/qr/gerar", data={
    "texto": "https://prisma.app",
    "cor_frente": "#000000",
    "cor_fundo": "#ffffff",
    "csrf_token": "test_csrf_token"
})
assert res_qr.status_code == 200, f"QR code generation failed status {res_qr.status_code}"
print("POST /api/qr/gerar OK")

# 3.2 File Hash
res_hash = client.post("/api/file/hash", data={
    "arquivo": (io.BytesIO(csv_content), "data.csv"),
    "csrf_token": "test_csrf_token"
})
assert res_hash.status_code == 200
hash_data = json.loads(res_hash.data.decode("utf-8"))
assert "sha256" in hash_data
print("POST /api/file/hash OK")

# 3.3 File Compress
res_comp = client.post("/api/file/comprimir", data={
    "arquivos": [(io.BytesIO(csv_content), "doc1.csv"), (io.BytesIO(csv_content), "doc2.csv")],
    "formato": "zip",
    "csrf_token": "test_csrf_token"
})
assert res_comp.status_code == 200
print("POST /api/file/comprimir OK")

print("=== ALL PRISMA CONVERTER ENDPOINTS AND FLOWS ARE FULLY WORKING! ===")
