"""Cada ataque confirmado na auditoria vira um teste."""
import io

import pytest
from flask.sessions import SecureCookieSessionInterface

from app import app
from core import config
from core.errors import ErroUsuario
from core.security import nome_seguro, validar_magic, validar_url_externa, verificar_zip_bomb
from tests.conftest import aguardar, arquivo, postar


def test_rotas_antigas_de_download_nao_existem():
    c = app.test_client()
    for caminho in ("/download/d", "/download/..%5Capp.py", "/download/..%5C..%5Csegredo.txt"):
        assert c.get(caminho).status_code == 404


def test_download_exige_id_de_job_valido():
    c = app.test_client()
    for caminho in ("/api/jobs/..%5Capp.py/download", "/api/jobs/" + "a" * 32 + "/download", "/api/jobs/xyz"):
        assert c.get(caminho).status_code == 404


def test_formato_nao_vira_caminho(cliente, amostras):
    r = postar(cliente, "/api/data/mesclar-planilhas", arquivos=[arquivo(amostras, "t.csv"), arquivo(amostras, "t.csv", "u.csv")],
               formato="/../../ESCRITO.xlsx")
    st = aguardar(cliente, r)
    assert st["nome_download"] == "Prisma_Planilhas_Mescladas.xlsx"
    assert not (config.DATA_DIR / "ESCRITO.xlsx").exists()


def test_post_sem_token_e_recusado():
    c = app.test_client()
    r = c.post("/api/file/hash", data={"arquivo": (io.BytesIO(b"x"), "x.txt")}, content_type="multipart/form-data")
    assert r.status_code == 403


def test_post_com_token_errado_e_recusado(cliente):
    r = cliente.post("/api/qr/gerar", data={"texto": "a", "csrf_token": "errado"})
    assert r.status_code == 403


@pytest.mark.parametrize("cabecalho", [{"Origin": "https://evil.example"}, {"Origin": "null"}, {"Sec-Fetch-Site": "cross-site"}])
def test_outros_sites_sao_bloqueados_mesmo_com_token(cliente, cabecalho):
    r = cliente.post("/api/qr/gerar", data={"texto": "a", "csrf_token": cliente.token}, headers=cabecalho)
    assert r.status_code == 403


def test_host_forjado_e_bloqueado():
    c = app.test_client()
    assert c.get("/health", headers={"Host": "evil.example"}).status_code == 403
    assert c.get("/health", headers={"Host": "127.0.0.1:5000"}).status_code == 200
    assert c.get("/health", headers={"Host": "localhost:5000"}).status_code == 200


def test_chave_secreta_nao_e_fixa():
    assert app.secret_key != "prisma_converter_local_app_secret_key"


def test_chave_gerada_e_aleatoria_e_persistente(tmp_path, monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setattr(config, "INSTANCE_DIR", tmp_path)
    monkeypatch.setattr(config, "UPLOAD_DIR", tmp_path / "u")
    monkeypatch.setattr(config, "DOWNLOAD_DIR", tmp_path / "d")
    primeira = config.carregar_chave_secreta()
    assert len(primeira) == 64 and config.carregar_chave_secreta() == primeira


def test_sessao_forjada_nao_le_arquivo_externo(tmp_path):
    """Mesmo com a chave em mãos, o nome do arquivo não vem mais da sessão."""
    ser = SecureCookieSessionInterface().get_signing_serializer(app)
    pasta = config.UPLOAD_DIR / ("a" * 32)
    pasta.mkdir(parents=True, exist_ok=True)
    cookie = ser.dumps({"pasta_upload": "a" * 32, "arquivo_nome": "..\\..\\..\\app.py", "arquivo_ext": "..\\..\\app.py"})
    c = app.test_client()
    c.set_cookie("session", cookie)
    assert c.get("/preview/" + "a" * 32).status_code == 403
    pasta.rmdir()


@pytest.mark.parametrize("url", ["http://127.0.0.1:5000/x", "http://localhost/x", "http://169.254.169.254/latest", "http://[::1]/x",
                                 "http://10.0.0.1/", "http://192.168.0.1/", "file:///c:/windows/win.ini", "ftp://x.com/a", "abc"])
def test_url_interna_e_recusada(url):
    with pytest.raises(ErroUsuario):
        validar_url_externa(url)


def test_baixar_link_interno_termina_em_erro(cliente):
    st = aguardar(cliente, postar(cliente, "/api/video/baixar-link", url="http://127.0.0.1:9/v.mp4"))
    assert st["status"] == "erro" and "rede local" in st["erro"]


def test_cabecalhos_de_seguranca():
    h = app.test_client().get("/").headers
    assert h["X-Content-Type-Options"] == "nosniff" and h["X-Frame-Options"] == "SAMEORIGIN"
    csp = h["Content-Security-Policy"]
    assert "script-src 'self'" in csp and "unsafe-inline" not in csp.split("script-src")[1].split(";")[0]


def test_paginas_nao_tem_script_inline_nem_recursos_externos():
    c = app.test_client()
    for pagina in ("/", "/conversor", "/ferramentas-avancadas", "/audio", "/video", "/historico", "/nao-existe"):
        html = c.get(pagina).get_data(as_text=True)
        assert " onclick=" not in html and " onchange=" not in html and " oninput=" not in html, pagina
        assert "fonts.googleapis" not in html, pagina


def test_tabela_escapa_html(cliente, tmp_path):
    csv = io.BytesIO(b"a,b\n<script>alert(1)</script>,2\n")
    r = cliente.post("/upload", data={"arquivo": (csv, "x.csv"), "csrf_token": cliente.token}, content_type="multipart/form-data")
    html = r.get_data(as_text=True)
    assert "<script>alert(1)" not in html and "&lt;script&gt;" in html


@pytest.mark.parametrize("entrada,esperado", [
    ("..\\..\\app.py", "app.py"), ("../../x.txt", "x.txt"), ("relatório final.pdf", "relatório final.pdf"),
    ("音乐.mp3", "音乐.mp3"), ("CON.txt", "arquivo.txt"), ("a<b>c.pdf", "a_b_c.pdf"), ("", "arquivo"), ("...", "arquivo"),
])
def test_nome_seguro(entrada, esperado):
    assert nome_seguro(entrada) == esperado


def test_validar_magic(tmp_path):
    p = tmp_path / "x"
    p.write_bytes(b"MZ\x90")
    assert not validar_magic(str(p), "pdf")
    p.write_bytes(b"%PDF-1.7")
    assert validar_magic(str(p), "pdf")
    p.write_bytes(b"[1,2]")
    assert validar_magic(str(p), "json")
    p.write_bytes(b"")
    assert not validar_magic(str(p), "csv")


def test_zip_bomb(tmp_path):
    import zipfile
    p = tmp_path / "b.docx"
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("x", b"\0" * (20 * 1024 * 1024))
    assert not verificar_zip_bomb(str(p))
    (tmp_path / "ruim.docx").write_bytes(b"PK\x03\x04lixo")
    assert not verificar_zip_bomb(str(tmp_path / "ruim.docx"))
