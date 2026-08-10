import os
import re
import time
import uuid
import shutil
import logging
import threading
import traceback
from datetime import datetime
from flask import Blueprint, request, render_template, send_file, jsonify, session, abort, Response, after_this_request
from werkzeug.utils import secure_filename

from core.security import (
    rate_limit_required, validar_csrf, validar_nome,
    validar_mime_type, validar_magic, verificar_zip_bomb, extrair_ip_cliente
)
from core.converter import (
    obter_conversoes, converter_arquivo, detectar_encoding
)
from core.storage import storage
from core.tasks import job_store, executar_conversao_async
from core.utils import (
    criar_pasta, pasta_path, erro_seguro, formatar_tamanho, DOWNLOAD_FOLDER
)

log = logging.getLogger(__name__)
converter_bp = Blueprint("converter", __name__)

_IS_RENDER = os.environ.get("RENDER") in ("true", "1") or bool(os.environ.get("RENDER_SERVICE_ID"))
_IS_DESKTOP = (os.environ.get("PRISMA_DESKTOP") == "1") or (not _IS_RENDER)
_IS_WEB = not _IS_DESKTOP

MAX_MB = int(os.environ.get("MAX_MB", "10")) if _IS_WEB else 0
MAX_OUTPUT_MB = int(os.environ.get("MAX_OUTPUT_MB", "50")) if _IS_WEB else 0

TIMEOUT_CONV = 120
TIMEOUT_PREVIEW = 40
MAX_PARALELAS = 1 if _IS_WEB else 5

_conversoes_ativas = 0
_lock_conv = threading.Lock()
_lock_contador = threading.Lock()
contador_conversoes = 0


def _gerar_preview_tabela(caminho: str, extensao: str, limite: int = None):
    try:
        import pandas as pd
        if extensao == "csv":
            enc = detectar_encoding(caminho)
            df = pd.read_csv(
                caminho,
                nrows=limite,
                sep=None, engine="python",
                encoding=enc,
                encoding_errors="replace",
                on_bad_lines="skip",
            )
        elif extensao == "xlsx":
            df = pd.read_excel(caminho, nrows=limite, engine="openpyxl")
        elif extensao == "xls":
            df = pd.read_excel(caminho, nrows=limite)
        elif extensao == "json":
            df = pd.read_json(caminho)
        else:
            return None

        df.columns = [str(c).strip() for c in df.columns]
        df = df.fillna("")

        if len(df.columns) > 10:
            df = df.iloc[:, :10]

        df = df.map(lambda v: (str(v)[:60] + "…") if len(str(v)) > 60 else str(v))
        return df.to_html(classes="tabela-preview", border=0, index=False, na_rep="")
    except Exception as e:
        log.warning(f"Preview tabela ({extensao}): {e}")
        return None


def _copiar_para_downloads_desktop(origem, nome_download):
    if not (os.environ.get("PRISMA_DESKTOP") == "1" or not os.environ.get("RENDER")):
        return
    try:
        user_profile = os.environ.get("USERPROFILE") or os.environ.get("HOME")
        if not user_profile:
            return
        downloads_sys = os.path.join(user_profile, "Downloads")
        if not os.path.exists(downloads_sys):
            return
        destino_sys = os.path.join(downloads_sys, nome_download)
        shutil.copy2(origem, destino_sys)
        log.info(f"[desktop] Arquivo copiado automaticamente para {destino_sys}")
    except Exception as e:
        log.warning(f"[desktop] Não foi possível copiar para a pasta Downloads: {e}")


def estimar_avisos_output(ext_origem, tamanho_bytes, conversoes, max_output_mb=50):
    if not _IS_WEB:
        return {}
    avisos = {}
    tamanho_mb = (tamanho_bytes / (1024 * 1024)) if tamanho_bytes else 0
    formatos_imagem = {"png", "jpg", "jpeg", "webp", "heic"}

    for dest in conversoes:
        if ext_origem in ("pdf", "pptx", "ppt", "docx") and dest in formatos_imagem:
            avisos[dest] = [
                f"Converter {ext_origem.upper()} para {dest.upper()} gera 1 imagem por página num arquivo ZIP.",
                f"Se o documento for longo, o download final pode exceder {max_output_mb} MB."
            ]
        elif tamanho_mb > 5.0 and dest in ("pdf", "docx", "xlsx", "png", "jpg"):
            avisos[dest] = [
                f"O arquivo original possui {tamanho_mb:.1f} MB.",
                f"O download final pode ficar grande (próximo de {max_output_mb} MB)."
            ]
    return avisos


@converter_bp.route("/preview/<pasta_uuid>/<preview_file>")

def preview_arquivo(pasta_uuid, preview_file):
    if not re.match(r'^[a-f0-9]{32}$', pasta_uuid):
        abort(400)
    if session.get("pasta_upload") != pasta_uuid:
        abort(403)
    if not re.match(r'^[a-zA-Z0-9_]+\.[a-zA-Z0-9]{1,10}$', preview_file):
        abort(400)
    c = os.path.join("uploads", pasta_uuid, preview_file)
    if not os.path.exists(c):
        abort(404)
    return send_file(c)


@converter_bp.route("/preview-convert/<pasta_uuid>/<destino>")
def preview_convert(pasta_uuid, destino):
    if not re.match(r'^[a-f0-9]{32}$', pasta_uuid):
        abort(400)
    if session.get("pasta_upload") != pasta_uuid:
        abort(403)
    if destino not in {"pdf","png","jpg","gif","csv","xlsx","docx","pptx","ppt","json","webp","heic","txt"}:
        abort(400)

    orientacao = request.args.get("orientacao", "retrato")
    if orientacao not in ("retrato", "paisagem"):
        orientacao = "retrato"

    extensao = session.get("arquivo_ext", "")
    arquivo_nome = session.get("arquivo_nome", "")
    pp = pasta_path(pasta_uuid)
    entrada = os.path.join(pp, arquivo_nome)

    if not os.path.exists(entrada):
        abort(404)
    if extensao == destino:
        return send_file(entrada)

    ori_key = f"_{orientacao}" if destino == "pdf" else ""
    prev_nome = f"prev_{destino}{ori_key}.{destino}"
    prev_path = os.path.join(pp, prev_nome)

    if not os.path.exists(prev_path):
        err = [None]; done = threading.Event()
        def _g():
            try:
                converter_arquivo(entrada, prev_path, extensao, destino, orientacao=orientacao)
            except Exception as e:
                err[0] = e
            finally:
                done.set()
        threading.Thread(target=_g, daemon=True).start()
        done.wait(timeout=TIMEOUT_PREVIEW)
        if not done.is_set():
            abort(504)
        if err[0] or not os.path.exists(prev_path):
            abort(500, description=erro_seguro(err[0]) if err[0] else "Erro ao gerar prévia")

    return send_file(prev_path)


@converter_bp.route("/preview-tabela/<pasta_uuid>/<destino>")
def preview_tabela(pasta_uuid, destino):
    if not re.match(r'^[a-f0-9]{32}$', pasta_uuid):
        abort(400)
    if session.get("pasta_upload") != pasta_uuid:
        abort(403)
    if destino not in ("csv", "xlsx", "json"):
        abort(400)

    extensao = session.get("arquivo_ext", "")
    arquivo_nome = session.get("arquivo_nome", "")
    pp = pasta_path(pasta_uuid)
    entrada = os.path.join(pp, arquivo_nome)

    if not os.path.exists(entrada):
        abort(404)

    if extensao in ("csv", "xlsx", "xls", "json"):
        alvo = entrada
        alvo_ext = extensao
    else:
        cache = os.path.join(pp, f"prev_{destino}.{destino}")
        if not os.path.exists(cache):
            try:
                converter_arquivo(entrada, cache, extensao, destino)
            except Exception as e:
                return Response(f"<p class='prev-erro-msg'>Erro ao converter: {erro_seguro(e)}</p>", status=500)
        alvo = cache
        alvo_ext = destino

    tabela = _gerar_preview_tabela(alvo, alvo_ext, limite=100)
    if tabela:
        return Response(tabela, content_type="text/html")
    return Response("<p class='prev-erro-msg'>Não foi possível gerar a tabela.</p>", status=500)


@converter_bp.route("/upload", methods=["POST"])
def upload():
    global contador_conversoes
    ip = extrair_ip_cliente(request)

    if not validar_csrf(request.form.get("csrf_token", "")):
        return render_template("index.html", erro="Token inválido. Recarregue a página.")

    try:
        if "arquivo" not in request.files:
            return render_template("index.html", erro="Nenhum arquivo enviado.")
        arq = request.files["arquivo"]
        if not arq or arq.filename == "":
            return render_template("index.html", erro="Selecione um arquivo.")

        nome_original = arq.filename.strip()
        if not validar_nome(nome_original):
            return render_template("index.html", erro="Nome de arquivo suspeito.")
        if "." not in nome_original:
            return render_template("index.html", erro="Arquivo sem extensão reconhecida.")

        ext = nome_original.rsplit(".", 1)[1].lower()

        if not validar_mime_type(arq, {ext}):
            return render_template("index.html", erro="Tipo de arquivo não permitido.")

        conteudo = arq.read()
        tamanho = len(conteudo)

        uid = criar_pasta()
        pp = pasta_path(uid)
        nome_i = f"arquivo.{ext}"
        cam = os.path.join(pp, nome_i)

        with open(cam, "wb") as f:
            f.write(conteudo)

        if not validar_magic(cam, ext):
            shutil.rmtree(pp, ignore_errors=True)
            return render_template("index.html", erro=f"Arquivo não parece ser '{ext.upper()}' válido.")

        if ext in ("zip",) and not verificar_zip_bomb(cam):
            shutil.rmtree(pp, ignore_errors=True)
            return render_template("index.html", erro="Arquivo ZIP suspeito: tamanho descomprimido excede o limite permitido.")

        conversoes = obter_conversoes(ext)
        if not conversoes:
            shutil.rmtree(pp, ignore_errors=True)
            return render_template("index.html", erro=f"Formato '.{ext}' não suportado.")

        session["pasta_upload"] = uid
        session["arquivo_nome"] = nome_i
        session["arquivo_ext"] = ext
        session["arquivo_tamanho"] = tamanho
        session.modified = True
        log.info(f"Upload OK: {nome_original} ({tamanho}b) — {ip}")

        preview_url = None
        preview_tipo = None
        tabela_html = None

        if ext == "pdf":
            preview_url = f"/preview/{uid}/{nome_i}"
            preview_tipo = "pdf"
        elif ext in ("png", "jpg", "jpeg", "webp", "heic"):
            preview_url = f"/preview/{uid}/{nome_i}"
            preview_tipo = "imagem"
        elif ext in ("csv", "xlsx", "xls", "json"):
            tabela_html = _gerar_preview_tabela(cam, ext, limite=500)
        else:
            prev_p = os.path.join(pp, "preview_source.pdf")
            err = [None]; done = threading.Event()
            def _p():
                try: converter_arquivo(cam, prev_p, ext, "pdf")
                except Exception as e: err[0] = e
                finally: done.set()
            threading.Thread(target=_p, daemon=True).start()
            done.wait(timeout=30)
            if not err[0] and os.path.exists(prev_p):
                preview_url = f"/preview/{uid}/preview_source.pdf"
                preview_tipo = "pdf"

        return render_template("index.html",

            arquivo=nome_i,
            nome_original=nome_original,
            origem=ext,
            conversoes=conversoes,
            preview_url=preview_url,
            preview_tipo=preview_tipo,
            tabela_html=tabela_html,
            avisos_output=estimar_avisos_output(ext, tamanho, conversoes, max_output_mb=MAX_OUTPUT_MB),
            max_output_mb=MAX_OUTPUT_MB,
        )


    except Exception as e:
        log.error(f"Upload error — {ip} — {traceback.format_exc()}")
        return render_template("index.html", erro=erro_seguro(e))


@converter_bp.route("/converter", methods=["POST"])
def converter():
    global _conversoes_ativas
    global contador_conversoes
    ip = extrair_ip_cliente(request)

    if not validar_csrf(request.form.get("csrf_token", "")):
        return render_template("index.html", erro="Token inválido.")

    with _lock_conv:
        if _conversoes_ativas >= MAX_PARALELAS:
            return render_template("index.html", erro="Servidor ocupado. Tente em instantes.")
        _conversoes_ativas += 1

    uid = session.get("pasta_upload", "")
    arquivo_nome = session.get("arquivo_nome", "")
    origem = request.form.get("origem", "")
    destino = request.form.get("destino", "")
    nome_original = request.form.get("nome_original", "arquivo")
    download_token = request.form.get("downloadToken", "")
    orientacao = request.form.get("orientacao", "retrato")
    if orientacao not in ("retrato", "paisagem"):
        orientacao = "retrato"

    if not re.match(r'^[a-f0-9]{32}$', uid):
        with _lock_conv: _conversoes_ativas -= 1
        return render_template("index.html", erro="Sessão inválida.")

    pp = pasta_path(uid)
    entrada = os.path.join(pp, arquivo_nome)
    if not os.path.exists(entrada):
        with _lock_conv: _conversoes_ativas -= 1
        return render_template("index.html", erro="Arquivo expirou. Envie novamente.")

    saida = None
    try:
        base = re.sub(r'[^\w\-_. ]', '_', os.path.splitext(secure_filename(nome_original))[0]).strip() or "arquivo"

        if destino in ("png", "jpg", "jpeg", "webp", "heic") and origem not in ("png", "jpg", "jpeg", "webp", "heic"):
            nome_saida = f"{base}_{destino.upper()}s.zip"
        else:
            nome_saida = f"{base}.{destino}"

        saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_{nome_saida}")

        err = [None]; done = threading.Event()
        def _c():
            try:
                converter_arquivo(entrada, saida, origem, destino, orientacao=orientacao)
            except Exception as e:
                err[0] = e
            finally:
                done.set()
        threading.Thread(target=_c, daemon=True).start()
        done.wait(timeout=TIMEOUT_CONV)

        if not done.is_set():
            return render_template("index.html", erro="Tempo excedido. Tente com um arquivo menor.")
        if err[0]:
            raise err[0]

        @after_this_request
        def deletar(resp):
            try: shutil.rmtree(pp, ignore_errors=True)
            except Exception: pass
            try:
                if saida and os.path.exists(saida): os.remove(saida)
            except Exception: pass
            return resp

        with _lock_contador:
            contador_conversoes += 1
        log.info(f"OK: {nome_original} | {origem.upper()}->{destino.upper()} | {ip}")

        if "historico" not in session:
            session["historico"] = []
        session["historico"].insert(0, {
            "nome": nome_original,
            "origem": origem.upper(),
            "destino": destino.upper(),
            "hora": datetime.now().strftime("%H:%M"),
        })
        session["historico"] = session["historico"][:5]
        session["pasta_upload"] = ""
        session.modified = True

        resp = send_file(saida, as_attachment=True, download_name=nome_saida)
        resp.headers["Cache-Control"] = "no-store"
        if download_token:
            is_secure = bool(os.environ.get("PORT"))
            resp.set_cookie("downloadToken", download_token, max_age=60, samesite="Lax", secure=is_secure)
        return resp

    except Exception as e:
        log.error(f"Conversão error — {traceback.format_exc()}")
        try: shutil.rmtree(pp, ignore_errors=True)
        except Exception: pass
        return render_template("index.html", erro=erro_seguro(e))
    finally:
        with _lock_conv:
            _conversoes_ativas -= 1


@converter_bp.route("/api/converter/async", methods=["POST"])
@rate_limit_required
def api_converter_async():
    global _conversoes_ativas
    if not validar_csrf(request.form.get("csrf_token", "")):
        return jsonify({"erro": "Token inválido. Recarregue a página."}), 403

    uid = session.get("pasta_upload", "")
    arquivo_nome = session.get("arquivo_nome", "")
    origem = request.form.get("origem", "").strip().lower()
    destino = request.form.get("destino", "").strip().lower()
    nome_original = request.form.get("nome_original", "arquivo")
    orientacao = request.form.get("orientacao", "retrato")
    autodestruicao = (request.form.get("autodestruicao") or session.get("prisma_retention_policy") or request.cookies.get("prisma_retention_policy", "15min")).strip().lower()

    if orientacao not in ("retrato", "paisagem"):
        orientacao = "retrato"
    if autodestruicao not in ("instant", "5min", "15min"):
        autodestruicao = "15min"

    if not re.match(r'^[a-f0-9]{32}$', uid):
        return jsonify({"erro": "Sessão inválida. Faça o upload novamente."}), 400
    if not origem or not destino:
        return jsonify({"erro": "Formato de origem ou destino não especificado."}), 400

    pp = pasta_path(uid)
    entrada = os.path.join(pp, arquivo_nome)
    if not os.path.exists(entrada):
        return jsonify({"erro": "Arquivo expirou. Faça o upload novamente."}), 400

    with _lock_conv:
        if _conversoes_ativas >= MAX_PARALELAS:
            return jsonify({"erro": "Servidor ocupado. Aguarde um momento e tente novamente."}), 503
        _conversoes_ativas += 1

    try:
        base = re.sub(r'[^\w\-_. ]', '_', os.path.splitext(secure_filename(nome_original))[0]).strip() or "arquivo"
        if destino in ("png", "jpg", "jpeg", "webp", "heic") and origem not in ("png", "jpg", "jpeg", "webp", "heic"):
            nome_saida = f"{base}_{destino.upper()}s.zip"
        else:
            nome_saida = f"{base}.{destino}"

        saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_{nome_saida}")

        job_id = executar_conversao_async(
            entrada=entrada,
            saida=saida,
            origem=origem,
            destino=destino,
            orientacao=orientacao,
            pasta_uid=uid,
            nome_download=nome_saida,
            timeout_segundos=TIMEOUT_CONV,
            autodestruicao=autodestruicao,
        )

        log.info("[async] Job %s iniciado: %s->%s (%s)", job_id[:8], origem, destino, nome_original)
        return jsonify({"ok": True, "job_id": job_id})

    except Exception as e:
        with _lock_conv:
            _conversoes_ativas -= 1
        log.error("[async] Erro ao iniciar job: %s", e)
        return jsonify({"erro": erro_seguro(e)}), 500


@converter_bp.route("/api/converter/status/<job_id>", methods=["GET"])
def api_converter_status(job_id):
    if not re.match(r'^[a-f0-9]{32}$', job_id):
        return jsonify({"erro": "Job ID inválido."}), 400

    job = job_store.get(job_id)
    if not job:
        return jsonify({"erro": "Job não encontrado ou expirado."}), 404

    return jsonify({
        "percent": job["percent"],
        "status": job["status"],
        "concluido": job["concluido"],
        "erro": job["erro"],
        "download_url": f"/api/converter/download/{job_id}" if job["concluido"] and not job["erro"] else None,
    })


@converter_bp.route("/api/converter/download/<job_id>", methods=["GET"])
def api_converter_download(job_id):
    global contador_conversoes
    if not re.match(r'^[a-f0-9]{32}$', job_id):
        return jsonify({"erro": "Job ID inválido."}), 400

    job = job_store.get(job_id)

    if not job:
        return render_template("index.html", erro="Download não encontrado ou expirado."), 404
    if job.get("erro"):
        return render_template("index.html", erro=job["erro"]), 400
    if not job.get("concluido") or not job.get("caminho_saida"):
        return render_template("index.html", erro="Conversão ainda não concluída."), 202

    saida = job["caminho_saida"]
    nome_download = job["nome_download"]
    pasta_uid = job["pasta_uid"]
    autodestruicao = job.get("autodestruicao", "15min")

    if not storage.existe(saida):
        job_store.remover(job_id)
        return render_template("index.html", erro="O arquivo convertido expirou. Faça o processo novamente."), 404

    if "historico" not in session:
        session["historico"] = []

    ext_destino = nome_download.rsplit(".", 1)[-1].upper() if "." in nome_download else "?"
    ext_origem = job.get("origem", "?").upper()
    timestamp_job = job.get("timestamp", time.time())

    expira_em = None
    if autodestruicao == "5min":
        expira_em = int(timestamp_job + 300)
    elif autodestruicao == "15min":
        expira_em = int(timestamp_job + 900)

    apagado_agora = (autodestruicao == "instant")

    item_existente = None
    for h in session["historico"]:
        if h.get("job_id") == job_id:
            item_existente = h
            break

    if item_existente:
        item_existente["apagado"] = item_existente.get("apagado") or apagado_agora
        item_existente["baixado"] = True
    else:
        novo_item = {
            "job_id": job_id,
            "nome": nome_download,
            "origem": ext_origem,
            "destino": ext_destino,
            "hora": datetime.now().strftime("%H:%M"),
            "autodestruicao": autodestruicao,
            "expira_em": expira_em,
            "caminho_saida": saida,
            "apagado": apagado_agora,
            "baixado": True,
            "download_url": f"/api/converter/download/{job_id}",
        }
        session["historico"].insert(0, novo_item)
        session["historico"] = session["historico"][:8]

    session["pasta_upload"] = ""
    session.modified = True

    if autodestruicao == "instant":
        job_store.remover(job_id)

        @after_this_request
        def cleanup_instant(response):
            def _remov():
                time.sleep(1)
                shutil.rmtree(pasta_path(pasta_uid), ignore_errors=True)
                try:
                    storage.remover(saida)
                except Exception:
                    pass
                with _lock_conv:
                    global _conversoes_ativas
                    _conversoes_ativas = max(0, _conversoes_ativas - 1)
            threading.Thread(target=_remov, daemon=True).start()
            return response
    else:
        @after_this_request
        def cleanup_lazy(response):
            with _lock_conv:
                global _conversoes_ativas
                _conversoes_ativas = max(0, _conversoes_ativas - 1)
            return response

    with _lock_contador:
        contador_conversoes += 1

    _copiar_para_downloads_desktop(saida, nome_download)
    resp = send_file(saida, as_attachment=True, download_name=nome_download)
    resp.headers["Cache-Control"] = "no-store"
    return resp
