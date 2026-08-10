import os
import uuid
import shutil
import logging
from flask import Blueprint, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename

from core.security import rate_limit_required, validar_csrf
from core.qr_tools import gerar_qrcode, ler_qrcode
from core.image_tools import extrair_paleta
from core.utils import (
    criar_pasta, pasta_path, limpar_pasta_upload,
    erro_seguro, registrar_saida_historico, DOWNLOAD_FOLDER
)

log = logging.getLogger(__name__)
tools_bp = Blueprint("tools", __name__)


@tools_bp.route("/api/qr/gerar", methods=["POST"])
@rate_limit_required
def api_gerar_qr():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    texto = request.form.get("texto", "").strip()
    if not texto:
        return render_template("pdf_tools.html", erro="Digite um texto ou URL para gerar o QR Code."), 400

    cor_frente = request.form.get("cor_frente", "#000000")
    cor_fundo = request.form.get("cor_fundo", "#FFFFFF")

    uid = criar_pasta()
    pp = pasta_path(uid)
    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_QRCode.png")
    try:
        gerar_qrcode(texto, saida, cor_frente=cor_frente, cor_fundo=cor_fundo)
        registrar_saida_historico(saida, "Prisma_QRCode.png", "TXT", "PNG", pasta_uid=uid)
        limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_QRCode.png")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_gerar_qr error: {e}")
        return render_template("pdf_tools.html", erro=erro_seguro(e)), 400


@tools_bp.route("/api/qr/ler", methods=["POST"])
@rate_limit_required
def api_ler_qr():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return jsonify({"erro": "Token inválido. Recarregue a página."}), 403

    f = request.files.get("arquivo")
    if not f or not f.filename:
        return jsonify({"erro": "Selecione uma imagem contendo um QR Code."}), 400

    uid = criar_pasta()
    pp = pasta_path(uid)
    nome_seguro = secure_filename(f.filename) or "qrcode_img.png"
    entrada = os.path.join(pp, nome_seguro)
    f.save(entrada)

    try:
        resultados = ler_qrcode(entrada)
        return jsonify({"codigos": resultados})
    except Exception as e:
        log.warning(f"api_ler_qr error: {e}")
        return jsonify({"erro": erro_seguro(e)}), 400
    finally:
        shutil.rmtree(pp, ignore_errors=True)


@tools_bp.route("/api/img/paleta", methods=["POST"])
@rate_limit_required
def api_paleta_cores():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return jsonify({"erro": "Token inválido. Recarregue a página."}), 403

    f = request.files.get("arquivo")
    if not f or not f.filename:
        return jsonify({"erro": "Selecione uma imagem para extrair a paleta de cores."}), 400

    n_cores = request.form.get("n_cores", "8")
    try:
        n_cores = min(max(int(n_cores), 3), 16)
    except ValueError:
        n_cores = 8

    uid = criar_pasta()
    pp = pasta_path(uid)
    nome_seguro = secure_filename(f.filename) or "imagem.png"
    entrada = os.path.join(pp, nome_seguro)
    f.save(entrada)

    try:
        paleta = extrair_paleta(entrada, n_cores=n_cores)
        return jsonify({"paleta": paleta})
    except Exception as e:
        log.warning(f"api_paleta_cores error: {e}")
        return jsonify({"erro": erro_seguro(e)}), 400
    finally:
        shutil.rmtree(pp, ignore_errors=True)
