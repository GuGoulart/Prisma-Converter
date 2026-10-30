"""Conversor: matriz de formatos, prévia e detecção do que está instalado."""
import io

import pytest

from core import converter as C
from tests.conftest import aguardar, arquivo, baixar, postar

AMOSTRA = {"csv": "t.csv", "xlsx": "t.xlsx", "json": "t.json", "pdf": "p3.pdf", "docx": "t.docx",
           "pptx": "t.pptx", "png": "i.png", "jpg": "i.jpg", "webp": "i.webp"}


def _pares_disponiveis():
    return [(o, d) for o in AMOSTRA for d in C.conversoes_disponiveis(o)[0]]


def _enviar(c, amostras, nome):
    r = postar(c, "/upload", arquivo=arquivo(amostras, nome))
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    return r.get_data(as_text=True)


@pytest.mark.parametrize("origem,destino", _pares_disponiveis())
def test_toda_conversao_oferecida_funciona(cliente, amostras, origem, destino):
    _enviar(cliente, amostras, AMOSTRA[origem])
    st = aguardar(cliente, postar(cliente, "/api/converter/async", destino=destino))
    assert st["erro"] is None, f"{origem}->{destino}: {st['erro']}"
    corpo = baixar(cliente, st)
    assert len(corpo) > 0
    if destino == "heic" and origem != "pdf":
        from PIL import Image
        assert Image.open(io.BytesIO(corpo)).format == "HEIF"


def test_conversao_indisponivel_e_recusada_com_motivo(cliente, amostras, monkeypatch):
    monkeypatch.setattr(C, "_OFFICE", {"word": False, "excel": False, "powerpoint": False})
    monkeypatch.setattr(C, "SOFFICE", None)
    assert C.requisito_faltando("docx", "pdf") == "Microsoft Word ou LibreOffice"
    assert C.requisito_faltando("pptx", "png") == "Microsoft PowerPoint ou LibreOffice"
    assert C.requisito_faltando("xlsx", "pdf") == "Microsoft Excel ou LibreOffice"
    assert C.requisito_faltando("csv", "json") is None
    assert C.requisito_faltando("pdf", "docx") is None
    _enviar(cliente, amostras, "t.docx")
    r = postar(cliente, "/api/converter/async", destino="pdf")
    assert r.status_code == 400 and "LibreOffice" in r.get_json()["erro"]


def test_pywin32_sem_office_nao_conta_como_motor():
    assert C._office_instalado("Prisma.ProgramaQueNaoExiste") is False


def test_tela_lista_apenas_o_disponivel(cliente, amostras, monkeypatch):
    monkeypatch.setattr(C, "_OFFICE", {"word": False, "excel": False, "powerpoint": False})
    monkeypatch.setattr(C, "SOFFICE", None)
    html = _enviar(cliente, amostras, "t.xlsx")
    assert 'value="csv"' in html and 'value="pdf"' not in html
    assert "LibreOffice" in html


def test_destino_fora_da_matriz_e_recusado(cliente, amostras):
    _enviar(cliente, amostras, "t.csv")
    assert postar(cliente, "/api/converter/async", destino="exe").status_code == 400
    assert postar(cliente, "/api/converter/async", destino="../x").status_code == 400


def test_converter_sem_upload_e_recusado(cliente):
    assert postar(cliente, "/api/converter/async", destino="pdf").status_code == 400


def test_mesmo_upload_vira_varios_formatos(cliente, amostras):
    _enviar(cliente, amostras, "t.csv")
    for destino in ("json", "xlsx", "docx"):
        assert len(baixar(cliente, aguardar(cliente, postar(cliente, "/api/converter/async", destino=destino)))) > 0


def test_pdf_para_png_entrega_zip_e_previa_entrega_imagem(cliente, amostras):
    _enviar(cliente, amostras, "p3.pdf")
    st = aguardar(cliente, postar(cliente, "/api/converter/async", destino="png"))
    assert st["nome_download"].endswith(".zip") and baixar(cliente, st)[:2] == b"PK"
    with cliente.session_transaction() as s:
        uid = s["pasta_upload"]
    r = cliente.get(f"/preview-convert/{uid}/png")
    assert r.status_code == 200 and r.get_data()[:4] == b"\x89PNG"
    r.close()


def test_previa_exige_a_sessao_dona_do_upload(cliente, amostras):
    from app import app
    _enviar(cliente, amostras, "p3.pdf")
    with cliente.session_transaction() as s:
        uid = s["pasta_upload"]
    outro = app.test_client()
    assert outro.get(f"/preview/{uid}").status_code == 403


def test_pdf_com_texto_vira_txt_sem_tesseract(amostras, tmp_path):
    saida = tmp_path / "s.txt"
    C.converter_arquivo(str(amostras / "p3.pdf"), str(saida), "pdf", "txt")
    assert "pagina 1" in saida.read_text(encoding="utf-8")


def test_nova_upload_apaga_a_anterior(cliente, amostras):
    from core import config
    _enviar(cliente, amostras, "t.csv")
    with cliente.session_transaction() as s:
        anterior = s["pasta_upload"]
    _enviar(cliente, amostras, "t.json")
    assert not (config.UPLOAD_DIR / anterior).exists()
