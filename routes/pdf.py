import os
import uuid
import logging
from flask import Blueprint, request, render_template, send_file
from werkzeug.utils import secure_filename

from core.security import rate_limit_required, validar_csrf
from core.pdf_tools import (
    mesclar_pdfs, dividir_pdf, proteger_pdf, desproteger_pdf,
    comprimir_pdf, adicionar_marca_dagua, extrair_imagens_pdf, manipular_paginas_pdf
)
from core.utils import (
    criar_pasta, pasta_path, limpar_pasta_upload,
    erro_seguro, registrar_saida_historico, DOWNLOAD_FOLDER
)

log = logging.getLogger(__name__)
pdf_bp = Blueprint("pdf", __name__)


@pdf_bp.route("/api/pdf/mesclar", methods=["POST"])
@rate_limit_required
def api_mesclar():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    arquivos = request.files.getlist("arquivos")
    if not arquivos or len(arquivos) < 2:
        return "Selecione pelo menos 2 arquivos", 400

    uid = criar_pasta()
    pp = pasta_path(uid)
    caminhos = []

    for f in arquivos:
        nome_seguro = secure_filename(f.filename)
        caminho = os.path.join(pp, nome_seguro)
        f.save(caminho)
        caminhos.append(caminho)

    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_Mesclado.pdf")
    try:
        mesclar_pdfs(caminhos, saida)
        registrar_saida_historico(saida, "Prisma_Mesclado.pdf", "PDF", "PDF", pasta_uid=uid)
        limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Mesclado.pdf")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_mesclar error: {e}")
        return render_template("pdf_tools.html", erro=erro_seguro(e)), 400


@pdf_bp.route("/api/pdf/dividir", methods=["POST"])
@rate_limit_required
def api_dividir():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    f = request.files.get("arquivo")
    if not f: return "Selecione um arquivo", 400

    modo = request.form.get("modo", "individual")
    parametro = request.form.get("parametro", "")

    uid = criar_pasta()
    pp = pasta_path(uid)
    entrada = os.path.join(pp, secure_filename(f.filename))
    f.save(entrada)

    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_Dividido.zip")
    try:
        dividir_pdf(entrada, saida, modo, parametro)
        registrar_saida_historico(saida, "Prisma_Dividido.zip", "PDF", "ZIP", pasta_uid=uid)
        limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Dividido.zip")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_dividir error: {e}")
        return render_template("pdf_tools.html", erro=erro_seguro(e)), 400


@pdf_bp.route("/api/pdf/proteger", methods=["POST"])
@rate_limit_required
def api_proteger():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    f = request.files.get("arquivo")
    senha = request.form.get("senha")
    if not f or not senha: return "Arquivo e senha são obrigatórios", 400

    uid = criar_pasta()
    pp = pasta_path(uid)
    entrada = os.path.join(pp, secure_filename(f.filename))
    f.save(entrada)

    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_Protegido.pdf")
    try:
        proteger_pdf(entrada, senha, saida)
        registrar_saida_historico(saida, "Prisma_Protegido.pdf", "PDF", "PDF", pasta_uid=uid)
        limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Protegido.pdf")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_proteger error: {e}")
        return render_template("pdf_tools.html", erro=erro_seguro(e)), 400


@pdf_bp.route("/api/pdf/desproteger", methods=["POST"])
@rate_limit_required
def api_desproteger():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    f = request.files.get("arquivo")
    senha = request.form.get("senha")
    if not f or not senha: return "Arquivo e senha são obrigatórios", 400

    uid = criar_pasta()
    pp = pasta_path(uid)
    entrada = os.path.join(pp, secure_filename(f.filename))
    f.save(entrada)

    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_Desprotegido.pdf")
    try:
        desproteger_pdf(entrada, senha, saida)
        registrar_saida_historico(saida, "Prisma_Desprotegido.pdf", "PDF", "PDF", pasta_uid=uid)
        limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Desprotegido.pdf")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_desproteger error: {e}")
        return render_template("pdf_tools.html", erro=erro_seguro(e)), 400


@pdf_bp.route("/api/pdf/comprimir", methods=["POST"])
@rate_limit_required
def api_comprimir():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    f = request.files.get("arquivo")
    nivel = request.form.get("nivel", "media")
    if not f: return "Selecione um arquivo", 400

    uid = criar_pasta()
    pp = pasta_path(uid)
    entrada = os.path.join(pp, secure_filename(f.filename))
    f.save(entrada)

    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_Comprimido.pdf")
    try:
        comprimir_pdf(entrada, saida, nivel=nivel)
        sz_orig = os.path.getsize(entrada) if os.path.exists(entrada) else None
        registrar_saida_historico(saida, "Prisma_Comprimido.pdf", "PDF", "PDF", tamanho_orig=sz_orig, pasta_uid=uid)
        limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Comprimido.pdf")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_comprimir error: {e}")
        return render_template("pdf_tools.html", erro=erro_seguro(e)), 400


@pdf_bp.route("/api/pdf/marca-dagua", methods=["POST"])
@rate_limit_required
def api_marca_dagua():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    f = request.files.get("arquivo")
    texto = request.form.get("texto")
    if not f or not texto: return "Arquivo e texto são obrigatórios", 400

    uid = criar_pasta()
    pp = pasta_path(uid)
    entrada = os.path.join(pp, secure_filename(f.filename))
    f.save(entrada)

    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_Marcado.pdf")
    try:
        adicionar_marca_dagua(entrada, texto, saida)
        registrar_saida_historico(saida, "Prisma_Marcado.pdf", "PDF", "PDF", pasta_uid=uid)
        limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Marcado.pdf")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_marca_dagua error: {e}")
        return render_template("pdf_tools.html", erro=erro_seguro(e)), 400


@pdf_bp.route("/api/pdf/extrair-imagens", methods=["POST"])
@rate_limit_required
def api_extrair_imagens():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    f = request.files.get("arquivo")
    if not f: return "Selecione um arquivo", 400

    uid = criar_pasta()
    pp = pasta_path(uid)
    entrada = os.path.join(pp, secure_filename(f.filename))
    f.save(entrada)

    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_Imagens_PDF.zip")
    try:
        extrair_imagens_pdf(entrada, saida)
        registrar_saida_historico(saida, "Prisma_Imagens_PDF.zip", "PDF", "ZIP", pasta_uid=uid)
        limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Imagens_PDF.zip")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_extrair_imagens error: {e}")
        return render_template("pdf_tools.html", erro=erro_seguro(e)), 400


@pdf_bp.route("/api/pdf/manipular-paginas", methods=["POST"])
@rate_limit_required
def api_manipular_paginas():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    f = request.files.get("arquivo")
    if not f: return "Selecione um arquivo", 400

    remover = request.form.get("remover", "")
    rotacionar = request.form.get("rotacionar", "")

    uid = criar_pasta()
    pp = pasta_path(uid)
    entrada = os.path.join(pp, secure_filename(f.filename))
    f.save(entrada)

    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_Paginas_Manipuladas.pdf")
    try:
        manipular_paginas_pdf(entrada, saida, remover, rotacionar)
        registrar_saida_historico(saida, "Prisma_Paginas_Manipuladas.pdf", "PDF", "PDF", pasta_uid=uid)
        limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Paginas_Manipuladas.pdf")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_manipular_paginas error: {e}")
        return render_template("pdf_tools.html", erro=erro_seguro(e)), 400
