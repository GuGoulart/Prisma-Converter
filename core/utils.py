"""
utils.py — Utilitários compartilhados para rotas e manipuladores de arquivos.
"""

import os
import time
import uuid
import datetime
import shutil
import threading
import logging
from flask import session
from core.storage import storage
from core.tasks import job_store

log = logging.getLogger(__name__)

UPLOAD_FOLDER = "uploads"
DOWNLOAD_FOLDER = "downloads"


def criar_pasta():
    """Cria uma subpasta temporária com UUID v4 em uploads/."""
    uid = uuid.uuid4().hex
    os.makedirs(os.path.join(UPLOAD_FOLDER, uid), exist_ok=True)
    return uid


def pasta_path(uid):
    """Retorna o caminho absoluto/relativo da pasta de upload por UUID."""
    return os.path.join(UPLOAD_FOLDER, uid)


def limpar_pasta_upload(pp):
    """Remove a pasta temporária de upload em uma thread separada em segundo plano."""
    def _remov():
        shutil.rmtree(pp, ignore_errors=True)
    threading.Thread(target=_remov, daemon=True).start()


def erro_seguro(e):
    """Sanitiza mensagens de erro internas para não expor paths ou detalhes do servidor."""
    msg = str(e)
    if "Poppler" in msg or "tesseract" in msg or "ghostscript" in msg:
        return "Erro no processamento interno do servidor."
    return msg[:120]


def formatar_tamanho(b):
    """Formata bytes em texto legível (B, KB, MB)."""
    if not isinstance(b, (int, float)):
        return "Indisponível"
    if b < 1024:
        return f"{b} B"
    if b < 1048576:
        return f"{b / 1024:.1f} KB"
    return f"{b / 1048576:.1f} MB"


def registrar_saida_historico(saida_path, nome_download, origem_fmt, destino_fmt, tamanho_orig=None, pasta_uid=None):
    """Registra qualquer arquivo gerado por ferramentas no histórico da sessão e no job_store."""
    job_id = uuid.uuid4().hex
    politica = session.get("prisma_retention_policy", "15min")
    agora = time.time()

    if politica == "instant":
        expira_em = None
    elif politica == "5min":
        expira_em = int(agora + 300)
    else:
        expira_em = int(agora + 900)

    job_data = {
        "job_id": job_id,
        "concluido": True,
        "percent": 100,
        "status": "Concluído",
        "erro": None,
        "caminho_saida": saida_path,
        "nome_original": nome_download,
        "pasta_uid": pasta_uid,
        "expira_em": expira_em,
    }
    job_store.salvar(job_id, job_data)

    item = {
        "job_id": job_id,
        "nome": nome_download,
        "origem": origem_fmt,
        "destino": destino_fmt,
        "data": datetime.datetime.now().strftime("%H:%M:%S"),
        "tamanho": formatar_tamanho(os.path.getsize(saida_path)) if os.path.exists(saida_path) else "N/A",
        "tamanho_orig": formatar_tamanho(tamanho_orig) if tamanho_orig else None,
        "caminho_saida": saida_path,
        "expira_em": expira_em,
        "autodestruicao": politica,
        "apagado": False,
        "baixado": False,
        "pasta_uid": pasta_uid,
    }
    if "historico" not in session or not isinstance(session["historico"], list):
        session["historico"] = []
    session["historico"].insert(0, item)
    session.modified = True
    return job_id
