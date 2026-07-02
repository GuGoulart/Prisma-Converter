import os
import uuid
import shutil
import subprocess
import fitz        # pymupdf
import pandas as pd
from pdf2docx import Converter
from PIL import Image

# ─────────────────────────────────────────
# Detecção de motor de conversão
# ─────────────────────────────────────────

try:
    import win32com.client
    import pythoncom
    _TEM_WIN32 = True
except ImportError:
    _TEM_WIN32 = False

try:
    import chardet
    _TEM_CHARDET = True
except ImportError:
    _TEM_CHARDET = False


def _encontrar_soffice():
    """Localiza o executável do LibreOffice."""
    # Tenta PATH do sistema primeiro
    for cmd in ("soffice", "libreoffice"):
        if shutil.which(cmd):
            return cmd

    # Caminhos comuns no Windows
    caminhos = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        r"C:\Program Files\LibreOffice 7\program\soffice.exe",
        r"C:\Program Files\LibreOffice 24\program\soffice.exe",
    ]
    for c in caminhos:
        if os.path.exists(c):
            return c
    return None


SOFFICE = _encontrar_soffice()

if _TEM_WIN32:
    MOTOR = "office"
elif SOFFICE:
    MOTOR = "libreoffice"
else:
    MOTOR = None

print(f"[Prisma] Motor de conversão: {MOTOR or 'NENHUM ENCONTRADO — instale o Office ou o LibreOffice'}")


# ─────────────────────────────────────────
# Conversões disponíveis por formato
# ─────────────────────────────────────────

CONVERSOES = {
    "csv":  ["xlsx", "pdf"],
    "xlsx": ["csv",  "pdf"],
    "pdf":  ["docx", "png"],
    "docx": ["pdf"],
    "ppt":  ["pdf"],
    "pptx": ["pdf"],
    "png":  ["pdf"],
    "jpg":  ["pdf"],
    "jpeg": ["pdf"],
}


def obter_conversoes(extensao):
    return CONVERSOES.get(extensao.lower(), [])


def obter_motor():
    return MOTOR


# ─────────────────────────────────────────
# Utilitários internos
# ─────────────────────────────────────────

def detectar_encoding(caminho):
    if _TEM_CHARDET:
        with open(caminho, "rb") as f:
            resultado = chardet.detect(f.read(100_000))
            return resultado.get("encoding") or "utf-8"
    return "utf-8"


def _soffice_convert(entrada, saida, formato_destino, timeout=120):
    """
    Converte usando LibreOffice headless.
    O LibreOffice gera o arquivo no mesmo diretório da saída,
    com o mesmo nome base da entrada + extensão de destino.
    """
    if not SOFFICE:
        raise RuntimeError("LibreOffice não encontrado. Instale e tente novamente.")

    saida_dir  = os.path.dirname(os.path.abspath(saida))
    nome_base  = os.path.splitext(os.path.basename(entrada))[0]
    saida_auto = os.path.join(saida_dir, f"{nome_base}.{formato_destino}")

    cmd = [
        SOFFICE,
        "--headless",
        "--norestore",
        "--convert-to", formato_destino,
        "--outdir", saida_dir,
        os.path.abspath(entrada),
    ]

    resultado = subprocess.run(
        cmd,
        capture_output=True,
        timeout=timeout
    )

    if resultado.returncode != 0:
        erro = resultado.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"LibreOffice falhou: {erro}")

    # Renomeia para o nome esperado se necessário
    if os.path.abspath(saida_auto) != os.path.abspath(saida):
        if os.path.exists(saida_auto):
            os.replace(saida_auto, saida)

    if not os.path.exists(saida):
        raise RuntimeError("LibreOffice não gerou o arquivo de saída.")


# ─────────────────────────────────────────
# CSV → XLSX
# ─────────────────────────────────────────

def csv_para_xlsx(entrada, saida):
    enc = detectar_encoding(entrada)
    df  = pd.read_csv(entrada, encoding=enc, sep=None, engine="python")
    df.to_excel(saida, index=False, engine="openpyxl")


# ─────────────────────────────────────────
# XLSX → CSV
# ─────────────────────────────────────────

def xlsx_para_csv(entrada, saida):
    df = pd.read_excel(entrada, engine="openpyxl")
    df.to_csv(saida, index=False)


# ─────────────────────────────────────────
# PDF → DOCX
# ─────────────────────────────────────────

def pdf_para_docx(entrada, saida):
    cv = Converter(entrada)
    try:
        cv.convert(saida)
    finally:
        cv.close()


# ─────────────────────────────────────────
# PDF → PNG  (primeira página)
# ─────────────────────────────────────────

def pdf_para_png(entrada, saida):
    doc = fitz.open(entrada)
    try:
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
        pix.save(saida)
    finally:
        doc.close()


# ─────────────────────────────────────────
# PNG / JPG → PDF
# ─────────────────────────────────────────

def imagem_para_pdf(entrada, saida):
    img = Image.open(entrada)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")
    img.save(saida, "PDF", resolution=150)


# ─────────────────────────────────────────
# DOCX → PDF
# ─────────────────────────────────────────

def docx_para_pdf(entrada, saida):
    if MOTOR == "office":
        _office_docx_para_pdf(entrada, saida)
    elif MOTOR == "libreoffice":
        _soffice_convert(entrada, saida, "pdf")
    else:
        raise RuntimeError("Nenhum motor disponível para esta conversão.")


def _office_docx_para_pdf(entrada, saida):
    pythoncom.CoInitialize()
    word = documento = None
    try:
        word      = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        documento = word.Documents.Open(os.path.abspath(entrada))
        documento.SaveAs(os.path.abspath(saida), FileFormat=17)
    finally:
        if documento:
            try: documento.Close(False)
            except Exception: pass
        if word:
            try: word.Quit()
            except Exception: pass
        pythoncom.CoUninitialize()


# ─────────────────────────────────────────
# XLSX → PDF
# ─────────────────────────────────────────

def xlsx_para_pdf(entrada, saida):
    if MOTOR == "office":
        _office_xlsx_para_pdf(entrada, saida)
    elif MOTOR == "libreoffice":
        _soffice_convert(entrada, saida, "pdf")
    else:
        raise RuntimeError("Nenhum motor disponível para esta conversão.")


def _office_xlsx_para_pdf(entrada, saida):
    pythoncom.CoInitialize()
    excel = workbook = None
    try:
        excel    = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        workbook = excel.Workbooks.Open(os.path.abspath(entrada))
        workbook.ExportAsFixedFormat(0, os.path.abspath(saida))
    finally:
        if workbook:
            try: workbook.Close(False)
            except Exception: pass
        if excel:
            try: excel.Quit()
            except Exception: pass
        pythoncom.CoUninitialize()


# ─────────────────────────────────────────
# CSV → PDF  (via XLSX temporário)
# ─────────────────────────────────────────

def csv_para_pdf(entrada, saida):
    enc       = detectar_encoding(entrada)
    saida_dir = os.path.dirname(saida)
    temp      = os.path.join(saida_dir, f"_tmp_{uuid.uuid4().hex}.xlsx")

    try:
        df = pd.read_csv(entrada, encoding=enc, sep=None, engine="python")
        df.to_excel(temp, index=False, engine="openpyxl")
        xlsx_para_pdf(temp, saida)
    finally:
        if os.path.exists(temp):
            try: os.remove(temp)
            except Exception: pass


# ─────────────────────────────────────────
# PPT / PPTX → PDF
# ─────────────────────────────────────────

def ppt_para_pdf(entrada, saida):
    if MOTOR == "office":
        _office_ppt_para_pdf(entrada, saida)
    elif MOTOR == "libreoffice":
        _soffice_convert(entrada, saida, "pdf")
    else:
        raise RuntimeError("Nenhum motor disponível para esta conversão.")


def _office_ppt_para_pdf(entrada, saida):
    pythoncom.CoInitialize()
    pp = apresentacao = None
    try:
        pp           = win32com.client.Dispatch("PowerPoint.Application")
        pp.Visible   = 1
        apresentacao = pp.Presentations.Open(os.path.abspath(entrada), WithWindow=False)
        apresentacao.SaveAs(os.path.abspath(saida), 32)
    finally:
        if apresentacao:
            try: apresentacao.Close()
            except Exception: pass
        if pp:
            try: pp.Quit()
            except Exception: pass
        pythoncom.CoUninitialize()


# ─────────────────────────────────────────
# Motor principal de despacho
# ─────────────────────────────────────────

_MAPA = {
    ("csv",  "xlsx"): csv_para_xlsx,
    ("xlsx", "csv"):  xlsx_para_csv,
    ("pdf",  "docx"): pdf_para_docx,
    ("pdf",  "png"):  pdf_para_png,
    ("docx", "pdf"):  docx_para_pdf,
    ("xlsx", "pdf"):  xlsx_para_pdf,
    ("csv",  "pdf"):  csv_para_pdf,
    ("ppt",  "pdf"):  ppt_para_pdf,
    ("pptx", "pdf"):  ppt_para_pdf,
    ("png",  "pdf"):  imagem_para_pdf,
    ("jpg",  "pdf"):  imagem_para_pdf,
    ("jpeg", "pdf"):  imagem_para_pdf,
}


def converter_arquivo(entrada, saida, origem, destino):
    origem  = origem.lower()
    destino = destino.lower()

    if not os.path.exists(entrada):
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {entrada}")

    funcao = _MAPA.get((origem, destino))
    if funcao is None:
        raise ValueError(f"Conversão '{origem.upper()} → {destino.upper()}' não é suportada.")

    funcao(entrada, saida)