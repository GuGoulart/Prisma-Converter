"""routes/history.py — Histórico de arquivos e política de autodestruição."""
import logging
import re
import uuid
import zipfile

from flask import Blueprint, jsonify, request, send_file

from core import config, settings
from core.jobs import apagar, jobs
from core.utils import nomes_unicos

log = logging.getLogger(__name__)
history_bp = Blueprint("history", __name__)


@history_bp.route("/api/historico/renovar/<job_id>", methods=["POST"])
def renovar(job_id):
    job = jobs.renovar(job_id) if re.match(r"^[a-f0-9]{32}$", job_id) else None
    if not job:
        return jsonify({"erro": "Este arquivo não pode mais ser renovado."}), 410
    return jsonify({"ok": True, "job_id": job.id, "expira_em": int(job.expira_em),
                    "mensagem": "Prazo de autodestruição renovado."})


@history_bp.route("/api/historico/set-politica", methods=["POST"])
def set_politica():
    dados = request.get_json(silent=True) or {}
    politica = settings.definir_politica_retencao(dados.get("politica") or "")
    return jsonify({"ok": True, "politica": politica})


@history_bp.route("/api/historico/zip-todos")
def zip_todos():
    ativos = jobs.arquivos_ativos()
    if not ativos:
        return jsonify({"erro": "Nenhum arquivo ativo disponível para download em lote."}), 404

    config.garantir_pastas()
    caminho = str(config.DOWNLOAD_DIR / f"lote_{uuid.uuid4().hex}.zip")
    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as zf:
        for job, nome in zip(ativos, nomes_unicos([j.nome_download for j in ativos])):
            zf.write(job.caminho_saida, arcname=nome)

    resposta = send_file(caminho, as_attachment=True, download_name="prisma_lote_arquivos.zip", max_age=0)
    resposta.direct_passthrough = False
    resposta.call_on_close(lambda: apagar(caminho))
    return resposta


@history_bp.route("/api/historico/destruir-tudo", methods=["POST"])
def destruir_tudo():
    total = jobs.destruir_todos()
    log.info("%d arquivos destruídos pelo usuário", total)
    return jsonify({"ok": True, "destruidos": total, "mensagem": "Todos os arquivos foram destruídos."})
