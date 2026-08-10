import os
import re
import time
import uuid
import logging
import zipfile
from flask import Blueprint, jsonify, request, session, send_file
from core.security import validar_csrf, csrf_required
from core.storage import storage
from core.tasks import job_store

log = logging.getLogger(__name__)
history_bp = Blueprint("history", __name__)


@history_bp.route("/api/historico/restaurar/<job_id>", methods=["POST"])
@csrf_required
def api_restaurar_historico(job_id):
    """Restaura a retenção de um arquivo no histórico enviado para 5min ou 15min."""
    if not re.match(r'^[a-f0-9]{32}$', job_id):
        return jsonify({"erro": "ID de arquivo inválido."}), 404

    hist = session.get("historico", [])
    item = None
    for h in hist:
        if h.get("job_id") == job_id:
            item = h
            break

    if not item:
        return jsonify({"erro": "Arquivo não encontrado no histórico da sessão."}), 404

    if item.get("destruido_manual"):
        return jsonify({"erro": "Este arquivo foi destruído manualmente e não pode ser restaurado."}), 410

    politica = item.get("autodestruicao", "15min")
    if politica not in ("5min", "15min"):
        return jsonify({"erro": "Este modo de autodestruição não permite restauração."}), 400

    caminho = item.get("caminho_saida")
    if caminho and not storage.existe(caminho):
        return jsonify({"erro": "O arquivo físico expirarou permanentemente e não pôde ser recuperado."}), 410

    agora = time.time()
    duracao = 300 if politica == "5min" else 900
    novo_expira = int(agora + duracao)

    item["expira_em"] = novo_expira
    item["apagado"] = False
    item["restaurado"] = True

    job_store.renovar_expiracao(job_id)
    session.modified = True

    log.info("[historico] Arquivo %s restaurado (+%ds retenção)", job_id[:8], duracao)
    return jsonify({
        "ok": True,
        "job_id": job_id,
        "expira_em": novo_expira,
        "autodestruicao": politica,
        "mensagem": "Arquivo restaurado com sucesso! Cronômetro de autodestruição reiniciado."
    })


@history_bp.route("/api/historico/set-politica", methods=["POST"])
@csrf_required
def api_set_politica():
    politica = request.json.get("politica") if request.is_json else request.form.get("politica")
    politica = (politica or "15min").strip().lower()
    if politica not in ("instant", "5min", "15min"):
        politica = "15min"
    session["prisma_retention_policy"] = politica
    session.modified = True
    resp = jsonify({"ok": True, "politica": politica, "mensagem": f"Política de retenção alterada para: {politica.upper()}"})
    resp.set_cookie("prisma_retention_policy", politica, max_age=31536000, samesite="Lax")
    return resp


@history_bp.route("/api/historico/set-seguranca", methods=["POST"])
@csrf_required
def api_set_seguranca_historico():
    payload = request.get_json(silent=True) or {}
    modo_seguro = bool(payload.get("modo_seguro", True))
    session["prisma_secure_wipe"] = modo_seguro
    session.modified = True
    return jsonify({"ok": True, "modo_seguro": modo_seguro})


@history_bp.route("/api/historico/alterar-modo/<job_id>", methods=["POST"])
@csrf_required
def api_alterar_modo_historico(job_id):
    if not re.match(r'^[a-f0-9]{32}$', job_id):
        return jsonify({"erro": "ID de arquivo inválido."}), 404

    politica = request.json.get("autodestruicao") if request.is_json else request.form.get("autodestruicao")
    politica = (politica or "15min").strip().lower()
    if politica not in ("instant", "5min", "15min"):
        politica = "15min"

    historico = session.get("historico", [])
    item = None
    for h in historico:
        if h.get("job_id") == job_id:
            item = h
            break

    if not item:
        return jsonify({"erro": "Arquivo não encontrado no histórico da sessão."}), 404

    agora = time.time()
    item["autodestruicao"] = politica
    if politica == "instant":
        item["expira_em"] = None
    elif politica == "5min":
        item["expira_em"] = int(agora + 300)
    elif politica == "15min":
        item["expira_em"] = int(agora + 900)

    session.modified = True
    log.info("[historico] Modo de autodestruição do job %s alterado para %s", job_id[:8], politica)
    return jsonify({
        "ok": True,
        "job_id": job_id,
        "autodestruicao": politica,
        "expira_em": item.get("expira_em"),
        "mensagem": f"Modo de autodestruição alterado para {politica.upper()}."
    })


@history_bp.route("/api/historico/zip-todos", methods=["GET"])
def api_historico_zip_todos():
    historico = session.get("historico", [])
    arquivos_para_zip = []

    for item in historico:
        if item.get("apagado") or item.get("autodestruicao") == "instant":
            continue
        caminho = item.get("caminho_saida")
        if not caminho or not storage.existe(caminho):
            job_id = item.get("job_id")
            if job_id:
                job = job_store.get(job_id)
                if job and job.get("caminho_saida") and storage.existe(job["caminho_saida"]):
                    caminho = job["caminho_saida"]
        if caminho and storage.existe(caminho):
            nome_download = item.get("nome", os.path.basename(caminho))
            arquivos_para_zip.append((caminho, nome_download))

    if not arquivos_para_zip:
        return jsonify({"erro": "Nenhum arquivo ativo disponível para download em lote."}), 404

    download_folder = "downloads"
    zip_filename = f"prisma_batch_{uuid.uuid4().hex[:8]}.zip"
    zip_path = os.path.join(download_folder, zip_filename)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for caminho, nome in arquivos_para_zip:
            try:
                if os.path.exists(caminho):
                    zf.write(caminho, arcname=nome)
                else:
                    zf.writestr(nome, storage.ler(caminho))
            except Exception as e:
                log.warning("[zip-todos] Erro ao adicionar %s: %s", caminho, e)

    if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
        return jsonify({"erro": "Falha ao gerar o arquivo de lote ZIP."}), 500

    return send_file(zip_path, as_attachment=True, download_name="prisma_lote_arquivos.zip")


@history_bp.route("/api/historico/destruir-tudo", methods=["POST"])
@csrf_required
def api_historico_destruir_tudo():
    historico = session.get("historico", [])
    destruidos = 0
    modo_seguro = session.get("prisma_secure_wipe", True)

    for item in historico:
        caminho = item.get("caminho_saida")
        job_id = item.get("job_id")

        if job_id:
            job = job_store.get(job_id)
            if job and job.get("caminho_saida"):
                caminho = job["caminho_saida"]
            job_store.remover(job_id)

        if caminho:
            try:
                storage.remover(caminho, modo_seguro=modo_seguro)
            except Exception:
                pass

        item["apagado"] = True
        item["expira_em"] = None
        item["destruido_manual"] = True
        destruidos += 1

    session.modified = True
    log.info("[historico] Todos os arquivos da sessão (%d) foram destruídos pelo usuário.", destruidos)
    return jsonify({"ok": True, "destruidos": destruidos, "mensagem": "Todos os arquivos foram destruídos permanentemente."})
