"""routes/converter.py — Conversor universal: upload com prévia e conversão assíncrona."""
import logging
import os
import re
import shutil
import uuid

from flask import Blueprint, Response, abort, jsonify, render_template, request, send_file, session
from werkzeug.exceptions import HTTPException

from core import config, settings
from core.converter import (CONVERSOES, conversoes_disponiveis, detectar_encoding,
                            obter_conversoes, requisito_faltando)
from core.errors import ErroUsuario
from core.jobs import apagar, jobs
from core.security import nome_seguro, obter_extensao, validar_entrada
from core.tarefas import executar_tarefa

log = logging.getLogger(__name__)
converter_bp = Blueprint("converter", __name__)

_UID = re.compile(r"^[a-f0-9]{32}$")
_IMAGENS = {"png", "jpg", "jpeg", "webp", "heic"}
_DIRETO_NO_NAVEGADOR = {"pdf", "png", "jpg", "jpeg", "webp"}
_DESTINOS_PREVIA = {"pdf", "png", "jpg"}
LIMITE_LINHAS_PREVIA = 500


def _pasta(uid: str) -> str:
    return str(config.UPLOAD_DIR / uid)


def _upload_da_sessao(uid: str | None = None) -> tuple[str, str, str]:
    """Retorna (pasta, arquivo, extensão) do upload atual, validando contra a sessão."""
    atual = session.get("pasta_upload", "")
    if not _UID.match(atual) or (uid is not None and uid != atual):
        abort(403)
    ext = session.get("arquivo_ext", "")
    if not re.fullmatch(r"[a-z0-9]{1,8}", ext):
        abort(403)
    pasta = _pasta(atual)
    entrada = os.path.join(pasta, f"arquivo.{ext}")
    if not os.path.exists(entrada):
        abort(404)
    return pasta, entrada, ext


def _tabela_html(caminho: str, ext: str, limite: int) -> str | None:
    """Monta a tabela com escape de HTML (to_html escapa o conteúdo das células)."""
    import pandas as pd
    try:
        if ext == "csv":
            df = pd.read_csv(caminho, nrows=limite, sep=None, engine="python",
                             encoding=detectar_encoding(caminho), encoding_errors="replace", on_bad_lines="skip")
        elif ext in ("xlsx", "xls"):
            df = pd.read_excel(caminho, nrows=limite)
        elif ext == "json":
            df = pd.read_json(caminho).head(limite)
        else:
            return None
        df = df.iloc[:, :10].fillna("")
        df.columns = [str(c).strip() for c in df.columns]
        df = df.map(lambda v: (str(v)[:60] + "…") if len(str(v)) > 60 else str(v))
        return df.to_html(classes="tabela-preview", border=0, index=False, na_rep="", escape=True)
    except Exception as e:
        log.warning("Prévia de tabela (%s): %s", ext, e)
        return None


@converter_bp.route("/upload", methods=["POST"])
def upload():
    def _erro(mensagem):
        return render_template("index.html", erro=mensagem), 400

    arquivo = request.files.get("arquivo")
    if not arquivo or not arquivo.filename:
        return _erro("Selecione um arquivo.")
    nome_original = nome_seguro(arquivo.filename)
    ext = obter_extensao(nome_original)
    if not obter_conversoes(ext):
        return _erro(f"Formato '.{ext}' não suportado." if ext else "Arquivo sem extensão reconhecida.")

    uid = uuid.uuid4().hex
    pasta = _pasta(uid)
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, f"arquivo.{ext}")
    try:
        arquivo.save(caminho)
        validar_entrada(caminho, ext)
    except ErroUsuario as e:
        apagar(pasta)
        return _erro(str(e))

    anterior = session.get("pasta_upload", "")
    if _UID.match(anterior or ""):
        apagar(_pasta(anterior))
    session.update(pasta_upload=uid, arquivo_ext=ext, arquivo_nome=nome_original)

    disponiveis, indisponiveis = conversoes_disponiveis(ext)
    preview_url = preview_tipo = tabela = None
    if ext in _DIRETO_NO_NAVEGADOR:
        preview_url, preview_tipo = f"/preview/{uid}", "pdf" if ext == "pdf" else "imagem"
    elif ext in ("csv", "xlsx", "xls", "json"):
        tabela = _tabela_html(caminho, ext, LIMITE_LINHAS_PREVIA)
    elif not requisito_faltando(ext, "pdf"):
        # Gerada sob demanda pelo <embed>: o upload não espera o Word ou o LibreOffice.
        preview_url, preview_tipo = f"/preview-convert/{uid}/pdf", "pdf"

    return render_template(
        "index.html", arquivo=f"arquivo.{ext}", nome_original=nome_original, origem=ext,
        conversoes=disponiveis, indisponiveis=indisponiveis,
        preview_url=preview_url, preview_tipo=preview_tipo, tabela_html=tabela, pasta_uuid=uid,
    )


@converter_bp.route("/preview/<uid>")
def preview_arquivo(uid):
    _pasta_atual, entrada, _ext = _upload_da_sessao(uid)
    return send_file(entrada, max_age=0)


def _gerar_previa(saida: str, tarefa: str, *args, **kwargs) -> None:
    if os.path.exists(saida):
        return
    try:
        executar_tarefa(tarefa, *args, timeout=config.TIMEOUT_PREVIEW, **kwargs)
    except ErroUsuario:
        # Uma tarefa interrompida pode deixar um arquivo pela metade, que viraria cache.
        apagar(saida)
        raise


@converter_bp.route("/preview-convert/<uid>/<destino>")
def preview_convert(uid, destino):
    if destino not in _DESTINOS_PREVIA:
        abort(400)
    pasta, entrada, ext = _upload_da_sessao(uid)
    if requisito_faltando(ext, destino):
        abort(409)
    orientacao = request.args.get("orientacao", "retrato")
    orientacao = orientacao if orientacao in ("retrato", "paisagem") else "retrato"
    if ext == destino:
        return send_file(entrada, max_age=0)

    saida = os.path.join(pasta, f"prev_{destino}_{orientacao}.{destino}")
    try:
        if destino == "pdf":
            _gerar_previa(saida, "converter", entrada, saida, ext, destino, orientacao=orientacao)
        else:
            _gerar_previa(saida, "preview.imagem", entrada, saida, ext, destino)
    except ErroUsuario as e:
        return Response(str(e), status=422, mimetype="text/plain")
    return send_file(saida, max_age=0)


@converter_bp.route("/preview-tabela/<uid>/<destino>")
def preview_tabela(uid, destino):
    if destino not in ("csv", "xlsx"):
        abort(400)
    pasta, entrada, ext = _upload_da_sessao(uid)
    alvo, alvo_ext = entrada, ext
    if ext not in ("csv", "xlsx", "xls", "json"):
        if requisito_faltando(ext, destino):
            abort(409)
        alvo, alvo_ext = os.path.join(pasta, f"prev_{destino}.{destino}"), destino
        try:
            _gerar_previa(alvo, "converter", entrada, alvo, ext, destino)
        except ErroUsuario as e:
            return Response(str(e), status=422, mimetype="text/plain")
    tabela = _tabela_html(alvo, alvo_ext, 100)
    if not tabela:
        return Response("Não foi possível gerar a tabela.", status=422, mimetype="text/plain")
    return Response(tabela, mimetype="text/html")


@converter_bp.route("/api/converter/async", methods=["POST"])
def converter_async():
    try:
        _pasta_atual, entrada, origem = _upload_da_sessao()
    except HTTPException:
        return jsonify({"erro": "Envie o arquivo novamente."}), 400

    destino = (request.form.get("destino") or "").strip().lower()
    if destino not in CONVERSOES.get("jpg" if origem == "jpeg" else origem, []):
        return jsonify({"erro": "Conversão não suportada."}), 400
    if falta := requisito_faltando(origem, destino):
        return jsonify({"erro": f"Esta conversão precisa de {falta}."}), 400
    orientacao = request.form.get("orientacao", "retrato")
    orientacao = orientacao if orientacao in ("retrato", "paisagem") else "retrato"

    base = os.path.splitext(session.get("arquivo_nome") or "arquivo")[0]
    empacotado = destino in _IMAGENS and origem not in _IMAGENS
    nome_saida = nome_seguro(f"{base}_{destino.upper()}s.zip" if empacotado else f"{base}.{destino}")

    # Cópia do original: o usuário pode converter o mesmo upload para vários formatos.
    uid = uuid.uuid4().hex
    pasta_entrada, pasta_saida = str(config.UPLOAD_DIR / uid), str(config.DOWNLOAD_DIR / uid)
    os.makedirs(pasta_entrada)
    os.makedirs(pasta_saida)
    copia = shutil.copy2(entrada, os.path.join(pasta_entrada, os.path.basename(entrada)))
    saida = os.path.join(pasta_saida, nome_saida)

    job = jobs.criar(nome_download=nome_saida, origem=origem.upper(), destino=destino.upper(),
                     politica=settings.politica_retencao(), pasta_entrada=pasta_entrada,
                     pasta_saida=pasta_saida, caminho_saida=saida)

    def trabalho(_job):
        executar_tarefa("converter", copia, saida, origem, destino, orientacao=orientacao, controle=job.controle)
        if not os.path.exists(saida) or os.path.getsize(saida) == 0:
            raise ErroUsuario("A conversão terminou sem gerar um arquivo.")

    jobs.submeter(job, trabalho)
    return jsonify({"ok": True, "job_id": job.id, "status_url": f"/api/jobs/{job.id}"}), 202
