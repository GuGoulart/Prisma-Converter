import os
import re
import uuid
import shutil
import logging
from flask import Blueprint, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename

from core.security import rate_limit_required, validar_csrf
from core.file_tools import (
    comprimir_arquivos, zip_com_senha, criptografar_arquivo,
    descriptografar_arquivo, calcular_hashes, renomear_em_lote
)
from core.converter import mesclar_planilhas
from core.utils import (
    criar_pasta, pasta_path, limpar_pasta_upload,
    erro_seguro, registrar_saida_historico, DOWNLOAD_FOLDER
)

log = logging.getLogger(__name__)
file_tools_bp = Blueprint("file_tools", __name__)


@file_tools_bp.route("/api/file/comprimir", methods=["POST"])
@rate_limit_required
def api_comprimir_arquivos():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    arquivos = request.files.getlist("arquivos")
    formato = request.form.get("formato", "zip")
    if not arquivos or len(arquivos) < 1:
        return "Selecione pelo menos 1 arquivo", 400
    if formato not in ("zip", "tar.gz"):
        formato = "zip"

    uid = criar_pasta()
    pp = pasta_path(uid)
    caminhos = []

    for f in arquivos:
        nome_seguro = secure_filename(f.filename)
        caminho = os.path.join(pp, nome_seguro)
        f.save(caminho)
        caminhos.append(caminho)

    ext_saida = "tar.gz" if formato == "tar.gz" else "zip"
    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_Comprimido.{ext_saida}")
    try:
        comprimir_arquivos(caminhos, saida, formato=formato)
        registrar_saida_historico(saida, f"Prisma_Comprimido.{ext_saida}", "FILE", ext_saida.upper(), pasta_uid=uid)
        limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name=f"Prisma_Comprimido.{ext_saida}")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_comprimir_arquivos error: {e}")
        return render_template("pdf_tools.html", erro=erro_seguro(e)), 400


@file_tools_bp.route("/api/file/zip-senha", methods=["POST"])
@rate_limit_required
def api_zip_senha():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    arquivos = request.files.getlist("arquivos")
    senha = request.form.get("senha", "")
    if not arquivos or len(arquivos) < 1:
        return "Selecione pelo menos 1 arquivo", 400
    if not senha:
        return "A senha é obrigatória", 400

    uid = criar_pasta()
    pp = pasta_path(uid)
    caminhos = []

    for f in arquivos:
        nome_seguro = secure_filename(f.filename)
        caminho = os.path.join(pp, nome_seguro)
        f.save(caminho)
        caminhos.append(caminho)

    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_Protegido.zip")
    try:
        zip_com_senha(caminhos, saida, senha)
        registrar_saida_historico(saida, "Prisma_Protegido.zip", "FILE", "ZIP", pasta_uid=uid)
        limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Protegido.zip")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_zip_senha error: {e}")
        return render_template("pdf_tools.html", erro=erro_seguro(e)), 400


@file_tools_bp.route("/api/file/criptografar", methods=["POST"])
@rate_limit_required
def api_criptografar():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    f = request.files.get("arquivo")
    senha = request.form.get("senha", "")
    if not f: return "Selecione um arquivo", 400
    if not senha: return "A senha é obrigatória", 400

    uid = criar_pasta()
    pp = pasta_path(uid)
    nome_seguro = secure_filename(f.filename)
    entrada = os.path.join(pp, nome_seguro)
    f.save(entrada)

    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_{nome_seguro}.enc")
    try:
        criptografar_arquivo(entrada, saida, senha)
        sz_orig = os.path.getsize(entrada) if os.path.exists(entrada) else None
        registrar_saida_historico(saida, f"Prisma_{nome_seguro}.enc", "FILE", "ENC", tamanho_orig=sz_orig, pasta_uid=uid)
        limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name=f"Prisma_{nome_seguro}.enc")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_criptografar error: {e}")
        return render_template("pdf_tools.html", erro=erro_seguro(e)), 400


@file_tools_bp.route("/api/file/descriptografar", methods=["POST"])
@rate_limit_required
def api_descriptografar():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    f = request.files.get("arquivo")
    senha = request.form.get("senha", "")
    if not f: return "Selecione um arquivo", 400
    if not senha: return "A senha é obrigatória", 400

    uid = criar_pasta()
    pp = pasta_path(uid)
    nome_seguro = secure_filename(f.filename)
    entrada = os.path.join(pp, nome_seguro)
    f.save(entrada)

    nome_dl = nome_seguro
    if nome_dl.endswith(".enc"):
        nome_dl = nome_dl[:-4]
    else:
        nome_dl = f"descriptografado_{nome_dl}"

    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_{nome_dl}")
    try:
        descriptografar_arquivo(entrada, saida, senha)
        sz_orig = os.path.getsize(entrada) if os.path.exists(entrada) else None
        registrar_saida_historico(saida, nome_dl, "ENC", "FILE", tamanho_orig=sz_orig, pasta_uid=uid)
        limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name=nome_dl)
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_descriptografar error: {e}")
        return render_template("pdf_tools.html", erro=erro_seguro(e)), 400


@file_tools_bp.route("/api/file/hash", methods=["POST"])
@rate_limit_required
def api_calcular_hash():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return jsonify({"erro": "Token inválido."}), 403

    f = request.files.get("arquivo")
    if not f: return jsonify({"erro": "Selecione um arquivo"}), 400

    uid = criar_pasta()
    pp = pasta_path(uid)
    entrada = os.path.join(pp, secure_filename(f.filename))
    f.save(entrada)

    try:
        hashes = calcular_hashes(entrada)
        hashes["nome"] = f.filename
        return jsonify(hashes)
    except Exception as e:
        log.warning(f"api_calcular_hash error: {e}")
        return jsonify({"erro": erro_seguro(e)}), 400
    finally:
        shutil.rmtree(pp, ignore_errors=True)


@file_tools_bp.route("/api/file/renomear-lote", methods=["POST"])
@rate_limit_required
def api_renomear_lote():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    arquivos = request.files.getlist("arquivos")
    padrao_raw = request.form.get("padrao", "arquivo_{n}")
    padrao = re.sub(r'[^\w\-_ {}]', '', padrao_raw).strip() or "arquivo_{n}"
    if len(padrao) > 100:
        padrao = padrao[:100]
    if not arquivos or len(arquivos) < 1:
        return "Selecione pelo menos 1 arquivo", 400

    uid = criar_pasta()
    pp = pasta_path(uid)
    caminhos = []

    for f in arquivos:
        nome_seguro = secure_filename(f.filename)
        caminho = os.path.join(pp, nome_seguro)
        f.save(caminho)
        caminhos.append(caminho)

    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_Renomeados.zip")
    try:
        renomear_em_lote(caminhos, padrao, saida)
        registrar_saida_historico(saida, "Prisma_Renomeados.zip", "FILE", "ZIP", pasta_uid=uid)
        limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Renomeados.zip")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_renomear_lote error: {e}")
        return render_template("pdf_tools.html", erro=erro_seguro(e)), 400


@file_tools_bp.route("/api/data/mesclar-planilhas", methods=["POST"])
@rate_limit_required
def api_mesclar_planilhas():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    arquivos = request.files.getlist("arquivos")
    formato = request.form.get("formato", "xlsx")
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

    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_Planilhas_Mescladas.{formato}")
    try:
        mesclar_planilhas(caminhos, saida, formato)
        registrar_saida_historico(saida, f"Prisma_Planilhas_Mescladas.{formato}", "XLSX", formato.upper(), pasta_uid=uid)
        limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name=f"Prisma_Planilhas_Mescladas.{formato}")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_mesclar_planilhas error: {e}")
        return render_template("pdf_tools.html", erro=erro_seguro(e)), 400
