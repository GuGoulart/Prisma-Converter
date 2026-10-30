"""routes/jobs.py — Status, cancelamento e download de qualquer tarefa."""
import re

from flask import Blueprint, abort, jsonify, send_file

from core.jobs import CONCLUIDO, jobs

jobs_bp = Blueprint("jobs", __name__)
_ID = re.compile(r"^[a-f0-9]{32}$")


def _job_ou_404(job_id: str):
    job = jobs.obter(job_id) if _ID.match(job_id) else None
    if not job:
        abort(404)
    return job


@jobs_bp.route("/api/jobs/<job_id>")
def status(job_id):
    return jsonify(_job_ou_404(job_id).para_api())


@jobs_bp.route("/api/jobs/<job_id>/cancelar", methods=["POST"])
def cancelar(job_id):
    _job_ou_404(job_id)
    return jsonify({"ok": jobs.cancelar(job_id)})


@jobs_bp.route("/api/jobs/<job_id>/download")
def download(job_id):
    job = _job_ou_404(job_id)
    if job.status != CONCLUIDO or job.apagado or not job.caminho_saida:
        return jsonify({"erro": "Este arquivo não está mais disponível."}), 410

    resposta = send_file(job.caminho_saida, as_attachment=True, download_name=job.nome_download, max_age=0)
    resposta.headers["Cache-Control"] = "no-store"
    if job.politica == "instant":
        # Apaga só depois do envio. Sem direct_passthrough=False o callback nunca é chamado.
        resposta.direct_passthrough = False
        resposta.call_on_close(lambda: jobs.destruir(job))
    return resposta
