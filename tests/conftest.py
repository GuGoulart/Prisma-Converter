"""Fixtures dos testes. Os dados ficam em pasta temporária: nunca tocam uploads/ e downloads/ reais."""
import io
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

_DADOS = tempfile.mkdtemp(prefix="prisma_tests_")
os.environ["PRISMA_DATA_DIR"] = _DADOS
os.environ.setdefault("SECRET_KEY", "chave-de-teste")

import pymupdf  # noqa: E402
import pytest  # noqa: E402

from app import app as flask_app  # noqa: E402
from core.jobs import jobs as gerenciador  # noqa: E402


def _ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], check=True)


@pytest.fixture(scope="session")
def amostras(tmp_path_factory) -> Path:
    from docx import Document
    from PIL import Image
    from pptx import Presentation
    import pandas as pd
    import qrcode

    d = tmp_path_factory.mktemp("amostras")
    _ffmpeg("-f", "lavfi", "-i", "sine=f=440:d=2", "-b:a", "128k", str(d / "a.mp3"))
    _ffmpeg("-f", "lavfi", "-i", "sine=f=440:d=2", "-metadata", "title=ÁGUA ÍNDIO Ý", "-b:a", "128k", str(d / "tag.mp3"))
    _ffmpeg("-f", "lavfi", "-i", "testsrc=d=2:s=320x240:r=10", "-f", "lavfi", "-i", "sine=d=2",
            "-pix_fmt", "yuv420p", "-shortest", str(d / "v.mp4"))
    Image.new("RGB", (400, 400), (200, 30, 30)).save(d / "i.png")
    Image.new("RGB", (200, 200), (30, 30, 200)).save(d / "i.jpg")
    Image.new("RGB", (200, 200), (30, 200, 30)).save(d / "i.webp")
    qrcode.make("<img src=x onerror=alert(1)>").save(d / "qr.png")
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    df.to_csv(d / "t.csv", index=False)
    df.to_excel(d / "t.xlsx", index=False)
    df.to_json(d / "t.json", orient="records")
    doc = Document()
    doc.add_paragraph("ola")
    doc.save(d / "t.docx")
    Presentation().save(d / "t.pptx")

    for nome, paginas in (("p3.pdf", 3), ("p12.pdf", 12)):
        pdf = pymupdf.open()
        for i in range(paginas):
            pg = pdf.new_page()
            pg.insert_text((72, 72), f"pagina {i + 1}")
            for y in (100, 150, 200):
                pg.draw_line((72, y), (400, y))
            for x in (72, 236, 400):
                pg.draw_line((x, 100), (x, 200))
            pg.insert_text((80, 130), "celA")
            pg.insert_text((250, 130), "celB")
            pg.insert_image(pymupdf.Rect(72, 320, 272, 520), filename=str(d / "i.png"))
        pdf.save(d / nome)
        pdf.close()
    return d


@pytest.fixture
def cliente():
    """Cliente com sessão e token CSRF válidos, como a interface."""
    c = flask_app.test_client()
    c.get("/conversor")
    with c.session_transaction() as s:
        c.token = s["csrf_token"]
    return c


def arquivo(amostras: Path, nome: str, como: str | None = None):
    return (io.BytesIO((amostras / nome).read_bytes()), como or nome)


def postar(c, rota, **campos):
    campos["csrf_token"] = c.token
    return c.post(rota, data=campos, content_type="multipart/form-data")


def aguardar(c, resposta, limite=120) -> dict:
    assert resposta.status_code == 202, resposta.get_data(as_text=True)
    url = resposta.get_json()["status_url"]
    fim = time.time() + limite
    while time.time() < fim:
        st = c.get(url).get_json()
        if st["concluido"]:
            return st
        time.sleep(0.05)
    raise AssertionError(f"Job não terminou: {st}")


def baixar(c, st) -> bytes:
    assert st["erro"] is None, st["erro"]
    r = c.get(st["download_url"])
    assert r.status_code == 200
    corpo = r.get_data()
    r.close()
    return corpo


@pytest.fixture(autouse=True)
def _isolar_jobs():
    yield
    while gerenciador.tem_trabalho_ativo():
        time.sleep(0.05)
    gerenciador.destruir_todos()


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_DADOS, ignore_errors=True)
