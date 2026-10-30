"""Cada ferramenta exercitada pela API, do upload ao download."""
import io
import os
import zipfile

import pymupdf
import pytest
from docx import Document

from tests.conftest import aguardar, arquivo, baixar, postar

CASOS = [
    ("/api/converter", "a.mp3", {"formato": "wav"}),
    ("/api/converter", "a.mp3", {"formato": "opus", "sample_rate": "44100", "canais": "1"}),
    ("/api/cortar", "a.mp3", {"inicio": "0", "fim": "1"}),
    ("/api/cortar", "a.mp3", {"inicio": "1"}),
    ("/api/volume", "a.mp3", {"ajuste": "+6"}),
    ("/api/volume", "a.mp3", {"ajuste": "normalizar"}),
    ("/api/volume", "tag.mp3", {"ajuste": "normalizar"}),
    ("/api/velocidade", "a.mp3", {"fator": "1.5"}),
    ("/api/inverter", "tag.mp3", {}),
    ("/api/video/mp4-para-mp3", "v.mp4", {}),
    ("/api/video/mp4-para-gif", "v.mp4", {"duracao": "1"}),
    ("/api/video/converter", "v.mp4", {"formato": "webm"}),
    ("/api/video/converter", "v.mp4", {"formato": "mkv"}),
    ("/api/video/compressor", "v.mp4", {"nivel": "whatsapp"}),
    ("/api/video/remover-audio", "v.mp4", {}),
    ("/api/video/capturar-foto", "v.mp4", {"tempo": "1", "formato": "jpg"}),
    ("/api/pdf/dividir", "p3.pdf", {}),
    ("/api/pdf/dividir", "p3.pdf", {"modo": "custom", "parametro": "1-2, 3"}),
    ("/api/pdf/proteger", "p3.pdf", {"senha": "x"}),
    ("/api/pdf/comprimir", "p3.pdf", {"nivel": "alta"}),
    ("/api/pdf/marca-dagua", "p3.pdf", {"texto": "abc"}),
    ("/api/pdf/extrair-imagens", "p3.pdf", {}),
    ("/api/pdf/manipular-paginas", "p3.pdf", {"remover": "1", "rotacionar": "2:90"}),
    ("/api/file/criptografar", "t.csv", {"senha": "x"}),
]


@pytest.mark.parametrize("rota,nome,campos", CASOS, ids=[f"{c[0]}-{i}" for i, c in enumerate(CASOS)])
def test_ferramenta_de_um_arquivo(cliente, amostras, rota, nome, campos):
    st = aguardar(cliente, postar(cliente, rota, arquivo=arquivo(amostras, nome), **campos))
    assert len(baixar(cliente, st)) > 0


@pytest.mark.parametrize("rota,campos", [
    ("/api/juntar", {"arquivos": ("a.mp3", "tag.mp3"), "formato": "ogg"}),
    ("/api/file/comprimir", {"arquivos": ("t.csv", "t.json"), "formato": "tar.gz"}),
    ("/api/file/zip-senha", {"arquivos": ("t.csv",), "senha": "x"}),
    ("/api/file/renomear-lote", {"arquivos": ("t.csv", "t.json"), "padrao": "doc_{n}"}),
    ("/api/data/mesclar-planilhas", {"arquivos": ("t.csv", "t.xlsx"), "formato": "json"}),
])
def test_ferramenta_de_varios_arquivos(cliente, amostras, rota, campos):
    campos = dict(campos)
    campos["arquivos"] = [arquivo(amostras, n) for n in campos["arquivos"]]
    st = aguardar(cliente, postar(cliente, rota, **campos))
    assert len(baixar(cliente, st)) > 0


def test_qr_gerar_e_ler(cliente, amostras):
    st = aguardar(cliente, postar(cliente, "/api/qr/gerar", texto="ola mundo"))
    png = baixar(cliente, st)
    st = aguardar(cliente, postar(cliente, "/api/qr/ler", arquivo=(io.BytesIO(png), "q.png")))
    assert st["dados"]["codigos"][0]["dados"] == "ola mundo"


def test_paleta_e_hash(cliente, amostras):
    st = aguardar(cliente, postar(cliente, "/api/img/paleta", arquivo=arquivo(amostras, "i.png")))
    assert st["dados"]["paleta"][0]["hex"] == "#c81e1e"
    st = aguardar(cliente, postar(cliente, "/api/file/hash", arquivo=arquivo(amostras, "t.csv")))
    assert len(st["dados"]["sha256"]) == 64 and st["dados"]["nome"] == "t.csv"


def test_criptografia_ida_e_volta(cliente, amostras):
    original = (amostras / "t.csv").read_bytes()
    enc = baixar(cliente, aguardar(cliente, postar(cliente, "/api/file/criptografar", arquivo=arquivo(amostras, "t.csv"), senha="s3nha")))
    st = aguardar(cliente, postar(cliente, "/api/file/descriptografar", arquivo=(io.BytesIO(enc), "t.csv.enc"), senha="s3nha"))
    assert st["nome_download"] == "t.csv" and baixar(cliente, st) == original
    st = aguardar(cliente, postar(cliente, "/api/file/descriptografar", arquivo=(io.BytesIO(enc), "t.csv.enc"), senha="errada"))
    assert "Senha incorreta" in st["erro"]


def test_desproteger_remove_a_senha_de_verdade(cliente, amostras):
    protegido = baixar(cliente, aguardar(cliente, postar(cliente, "/api/pdf/proteger", arquivo=arquivo(amostras, "p3.pdf"), senha="abc")))
    assert pymupdf.open(stream=protegido, filetype="pdf").needs_pass
    st = aguardar(cliente, postar(cliente, "/api/pdf/desproteger", arquivo=(io.BytesIO(protegido), "x.pdf"), senha="errada"))
    assert st["erro"] == "Senha incorreta."
    livre = baixar(cliente, aguardar(cliente, postar(cliente, "/api/pdf/desproteger", arquivo=(io.BytesIO(protegido), "x.pdf"), senha="abc")))
    assert not pymupdf.open(stream=livre, filetype="pdf").needs_pass


def test_comprimir_mantem_imagens_legiveis(cliente, amostras):
    saida = baixar(cliente, aguardar(cliente, postar(cliente, "/api/pdf/comprimir", arquivo=arquivo(amostras, "p3.pdf"), nivel="alta")))
    doc = pymupdf.open(stream=saida, filetype="pdf")
    pix = doc[0].get_pixmap(clip=pymupdf.Rect(100, 350, 200, 450))
    r, g, b = pix.pixel(10, 10)
    assert r > 150 and g < 90 and b < 90, "a imagem deve seguir vermelha depois de recomprimida"


def test_mesclar_arquivos_com_o_mesmo_nome(cliente, amostras):
    r = postar(cliente, "/api/pdf/mesclar", arquivos=[arquivo(amostras, "p3.pdf"), arquivo(amostras, "p12.pdf", "p3.pdf")])
    assert pymupdf.open(stream=baixar(cliente, aguardar(cliente, r)), filetype="pdf").page_count == 15


def test_pacote_preserva_nomes_e_nao_colide(cliente, amostras):
    r = postar(cliente, "/api/file/comprimir", arquivos=[arquivo(amostras, "t.csv", "relatório.csv"), arquivo(amostras, "t.json", "relatório.csv")])
    with zipfile.ZipFile(io.BytesIO(baixar(cliente, aguardar(cliente, r)))) as z:
        assert sorted(z.namelist()) == ["relatório (2).csv", "relatório.csv"]


@pytest.mark.parametrize("rota,campos,nome", [
    ("/api/inverter", {}, "音乐.mp3"),
    ("/api/pdf/dividir", {}, "文件.pdf"),
])
def test_nomes_nao_latinos(cliente, amostras, rota, campos, nome):
    origem = "a.mp3" if nome.endswith("mp3") else "p3.pdf"
    st = aguardar(cliente, postar(cliente, rota, arquivo=arquivo(amostras, origem, nome), **campos))
    assert len(baixar(cliente, st)) > 0


def test_erro_de_midia_e_legivel(cliente):
    st = aguardar(cliente, postar(cliente, "/api/inverter", arquivo=(io.BytesIO(b"\xff\xfb" + os.urandom(2000)), "ruim.mp3")))
    assert "corrompido" in st["erro"] and "\\" not in st["erro"]


def test_tipo_errado_e_recusado(cliente, amostras):
    r = postar(cliente, "/api/pdf/dividir", arquivo=arquivo(amostras, "t.csv"))
    assert r.status_code == 400
    r = postar(cliente, "/api/pdf/dividir", arquivo=arquivo(amostras, "t.csv", "falso.pdf"))
    assert r.status_code == 400 and "não corresponde" in r.get_json()["erro"]


def test_pdf_com_mais_de_10_paginas_mantem_tabelas_e_imagens(cliente, amostras):
    from core.converter import pdf_para_docx
    saida = amostras / "saida12.docx"
    pdf_para_docx(str(amostras / "p12.pdf"), str(saida))
    doc = Document(saida)
    assert len(doc.tables) >= 12 and len(doc.inline_shapes) >= 12


@pytest.mark.parametrize("campos,mensagem", [
    ({"inicio": "abc"}, "Tempo inválido"),
    ({"inicio": "5", "fim": "1"}, "maior que o tempo inicial"),
])
def test_validacao_antes_de_processar(cliente, amostras, campos, mensagem):
    r = postar(cliente, "/api/cortar", arquivo=arquivo(amostras, "a.mp3"), **campos)
    assert r.status_code == 400 and mensagem in r.get_json()["erro"]


@pytest.mark.parametrize("valor", ["nan", "inf", "-1", "abc"])
def test_numeros_invalidos_em_foto(cliente, amostras, valor):
    assert postar(cliente, "/api/video/capturar-foto", arquivo=arquivo(amostras, "v.mp4"), tempo=valor).status_code == 400
