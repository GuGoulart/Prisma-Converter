from flask import (Flask, render_template, request, send_file,
                   session, after_this_request, abort, Response,
                   redirect, url_for, jsonify)
from core.converter import obter_conversoes, converter_arquivo, obter_motor, detectar_encoding, mesclar_planilhas
from core.pdf_tools import mesclar_pdfs, dividir_pdf, proteger_pdf, desproteger_pdf, comprimir_pdf, adicionar_marca_dagua, extrair_imagens_pdf, manipular_paginas_pdf
from werkzeug.utils import secure_filename
from datetime import datetime
from collections import defaultdict
from threading import Lock
from core.security import (gerar_csrf, validar_csrf, verificar_rate_limit,
                           validar_nome, validar_magic, rate_limit_required,
                           extrair_ip_cliente, validar_mime_type, verificar_zip_bomb)
from core.cleanup import iniciar_limpeza
from core.tasks import job_store, executar_conversao_async
from core.storage import storage
import sys
from dotenv import load_dotenv

import os, re, secrets, shutil, time, uuid, logging, threading, traceback, zipfile, hashlib

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
log = logging.getLogger(__name__)

def _formatar_tamanho(b):
    if not isinstance(b, (int, float)):
        return "Indisponível"
    if b < 1024:
        return f"{b} B"
    if b < 1048576:
        return f"{b / 1024:.1f} KB"
    return f"{b / 1048576:.1f} MB"

load_dotenv()

if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    app = Flask(__name__,
                template_folder=os.path.join(bundle_dir, 'templates'),
                static_folder=os.path.join(bundle_dir, 'static'))
else:
    app = Flask(__name__)

try:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
except Exception:
    pass

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
_sec_key = (os.environ.get("SECRET_KEY") or "").strip()
if not _sec_key:
    if os.environ.get("PORT") and not app.debug:
        log.warning("[seguranca] SECRET_KEY não configurada no ambiente de produção. Gerando chave temporária randômica.")
        _sec_key = secrets.token_hex(32)
    else:
        _sec_key = "prisma_converter_default_secret_key_dev_2026"
app.secret_key = _sec_key

UPLOAD_FOLDER   = "uploads"
DOWNLOAD_FOLDER = "downloads"
MAX_MB          = 15
TIMEOUT_CONV    = 120
TIMEOUT_PREVIEW = 40

app.config["UPLOAD_FOLDER"]      = UPLOAD_FOLDER
app.config["DOWNLOAD_FOLDER"]    = DOWNLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
if os.environ.get("PORT"):
    app.config["SESSION_COOKIE_SECURE"] = True

os.makedirs(UPLOAD_FOLDER,   exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def obter_pasta_downloads_usuario():
    pasta = os.path.join(os.path.expanduser('~'), 'Downloads')
    if os.name == 'nt':
        try:
            import winreg
            sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                pasta = winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
        except Exception:
            pass
    return pasta

def copiar_para_downloads_desktop(caminho_arquivo, download_name):
    if os.environ.get("PRISMA_DESKTOP") == "1" and os.path.exists(caminho_arquivo):
        try:
            pasta_dl = obter_pasta_downloads_usuario()
            os.makedirs(pasta_dl, exist_ok=True)
            dest = os.path.join(pasta_dl, download_name)
            shutil.copy2(caminho_arquivo, dest)
            logging.info(f"[desktop-app] Arquivo copiado para a pasta Downloads: {dest}")
        except Exception as e:
            logging.warning(f"[desktop-app] Erro ao copiar para Downloads: {e}")

@app.context_processor
def inject_desktop_flag():
    return dict(
        is_desktop_app=bool(os.environ.get("PRISMA_DESKTOP") == "1"),
        pasta_downloads_usuario=obter_pasta_downloads_usuario()
    )

contador_conversoes = 0
_lock_contador      = Lock()  # QC-005: protege o contador contra race conditions

# ── Request ID para correlação de logs ────────────────────────────────────────
_request_id_local = threading.local()

class _RequestIdFormatter(logging.Formatter):
    """Garante que request_id sempre exista no record de log sem lançar KeyError/ValueError."""
    def format(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = getattr(_request_id_local, "request_id", "-")
        return super().format(record)

_log_handler = logging.StreamHandler(sys.stdout)
_log_handler.setFormatter(_RequestIdFormatter(
    fmt="%(asctime)s [%(levelname)s] [%(request_id)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
logging.basicConfig(level=logging.INFO, handlers=[_log_handler])
log = logging.getLogger(__name__)

@app.before_request
def _set_request_id():
    _request_id_local.request_id = uuid.uuid4().hex[:8]

_conversoes_ativas = 0
_lock_conv         = Lock()

def _get_env_int(key, default):
    val = (os.environ.get(key) or "").strip()
    return int(val) if val.isdigit() else default

MAX_PARALELAS = _get_env_int("MAX_PARALELAS", 4)


LIMITES_POR_TIPO = {
    "pdf":  MAX_MB * 1024 * 1024,
    "docx": MAX_MB * 1024 * 1024,
    "xlsx": MAX_MB * 1024 * 1024,
    "pptx": MAX_MB * 1024 * 1024,
    "csv":  MAX_MB * 1024 * 1024,
    "ppt":  MAX_MB * 1024 * 1024,
    "doc":  MAX_MB * 1024 * 1024,
    "xls":  MAX_MB * 1024 * 1024,
    "png":  MAX_MB * 1024 * 1024,
    "jpg":  MAX_MB * 1024 * 1024,
    "jpeg": MAX_MB * 1024 * 1024,
    "json": MAX_MB * 1024 * 1024,
    "webp": MAX_MB * 1024 * 1024,
    "heic": MAX_MB * 1024 * 1024,
    "mp4":  MAX_MB * 1024 * 1024,
    "mp3":  MAX_MB * 1024 * 1024,
    "enc":  MAX_MB * 1024 * 1024,
}
NOMES_LIMITES = {k: f"{MAX_MB} MB" for k in LIMITES_POR_TIPO}


# ── Flask-Limiter com Redis (quando disponível) ──────────────────────────────────────
# Modo: sem REDIS_URL → rate limiting in-memory (limitado a uma instância).
#        com REDIS_URL → rate limiting distribuído via Redis (escala horizontal).
_REDIS_URL = (os.environ.get("REDIS_URL") or "").strip()
try:
    from flask_limiter import Limiter
    def _limiter_key():
        return extrair_ip_cliente()  # req=None → usa flask.request do contexto
    _limiter_storage_uri = _REDIS_URL if (_REDIS_URL and _REDIS_URL.startswith("redis")) else "memory://"
    limiter = Limiter(
        app=app,
        key_func=_limiter_key,
        default_limits=["1000 per day", "300 per hour"],
        storage_uri=_limiter_storage_uri,
    )
    log.info("[limiter] Flask-Limiter ativo (%s)", "Redis" if (_REDIS_URL and _REDIS_URL.startswith("redis")) else "in-memory")
except ImportError:
    limiter = None
    log.warning("[limiter] flask-limiter não instalado — usando rate limiting custom.")
except Exception as _le:
    limiter = None
    log.error("[limiter] Erro ao inicializar Flask-Limiter: %s — usando rate limiting custom.", _le)

# ── Segurança ─────────────────────────────────────────────────

@app.after_request
def cabecalhos_seguranca(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]         = "SAMEORIGIN"
    response.headers["X-XSS-Protection"]        = "1; mode=block"
    response.headers["Referrer-Policy"]          = "no-referrer"
    response.headers["Permissions-Policy"]       = "camera=(), microphone=(), geolocation=()"
    # SEG-009: HSTS apenas em produção (evita travar HTTP em desenvolvimento local)
    if os.environ.get("PORT") and not app.debug:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # AUD-001: CSP unificado (merge de cabecalhos_seguranca + add_security_headers removido)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com data:; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com"
    )
    return response


# SEG-007: Sanitiza mensagens de erro — nunca expõe str(e) bruto ao usuário
_ERROS_CONHECIDOS = {
    "password": "Senha incorreta ou arquivo não está protegido.",
    "encrypted": "O arquivo está criptografado. Forneça a senha correta.",
    "no objects": "O PDF parece estar corrompido ou vazio.",
    "not a pdf": "O arquivo enviado não é um PDF válido.",
    "bad decrypt": "Senha incorreta.",
    "permission": "O PDF não permite esta operação.",
    "cannot open": "Não foi possível abrir o arquivo.",
    "zero-size": "O arquivo está vazio.",
}

def _erro_seguro(e: Exception) -> str:
    """Retorna mensagem amigável sem expor detalhes internos."""
    msg = str(e).lower()
    for chave, amigavel in _ERROS_CONHECIDOS.items():
        if chave in msg:
            return amigavel
    return "Ocorreu um erro ao processar o arquivo. Verifique se ele está corrompido ou tente novamente."






def criar_pasta():
    uid = uuid.uuid4().hex
    os.makedirs(os.path.join(UPLOAD_FOLDER, uid), exist_ok=True)
    return uid

def pasta_path(uid):
    return os.path.join(UPLOAD_FOLDER, uid)


# ── Preview de tabela ─────────────────────────────────────────

def gerar_preview_tabela(caminho: str, extensao: str, limite: int = None):
    """
    Gera HTML de tabela para CSV/XLSX.
    limite=None → sem limite de linhas (CSV completo).
    limite=N    → máx N linhas.
    """
    try:
        import pandas as pd
        if extensao == "csv":
            enc = detectar_encoding(caminho)
            df  = pd.read_csv(
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
            # AUD-006: xls (formato binário legado) não suporta openpyxl — auto-detect engine
            df = pd.read_excel(caminho, nrows=limite)
        elif extensao == "json":
            df = pd.read_json(caminho)
        else:
            return None

        df.columns = [str(c).strip() for c in df.columns]
        df = df.fillna("")

        # Trunca colunas (máx 10)
        if len(df.columns) > 10:
            df = df.iloc[:, :10]

        # Trunca texto longo por célula (pandas 3.0+: .map em vez de .applymap)
        df = df.map(lambda v: (str(v)[:60] + "…") if len(str(v)) > 60 else str(v))

        return df.to_html(classes="tabela-preview", border=0, index=False, na_rep="")

    except Exception as e:
        log.warning(f"Preview tabela ({extensao}): {e}")
        return None


# ── Limpeza automática ────────────────────────────────────────

iniciar_limpeza(UPLOAD_FOLDER, DOWNLOAD_FOLDER)


# ── Context processor ─────────────────────────────────────────

@app.context_processor
def inject_globals():
    from core.converter import CONVERSOES
    if "prisma_retention_policy" not in session:
        session["prisma_retention_policy"] = "15min"
    
    current_policy = session.get("prisma_retention_policy", "15min")
    if current_policy not in ("instant", "5min", "15min"):
        current_policy = "15min"
        session["prisma_retention_policy"] = "15min"

    hist = session.get("historico", [])
    agora = time.time()
    for item in hist:
        expira_em = item.get("expira_em")
        caminho = item.get("caminho_saida")
        destruido = item.get("destruido_manual", False)
        baixado = item.get("baixado", False)
        policy = item.get("autodestruicao", "15min")

        if destruido:
            item["apagado"] = True
        elif policy == "instant" and baixado:
            item["apagado"] = True
        elif expira_em and agora > expira_em:
            item["apagado"] = True
        elif caminho and not storage.existe(caminho):
            item["apagado"] = True
        else:
            item["apagado"] = False

    return dict(
        contador=contador_conversoes,
        historico=hist,
        retencao_padrao=current_policy,
        motor=obter_motor(),
        csrf_token=gerar_csrf(),
        todas_conversoes=CONVERSOES,
    )


@app.errorhandler(413)
def arquivo_grande(e):
    return render_template("index.html",
                           erro=f"Arquivo muito grande. Limite: {MAX_MB} MB."), 413

@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def erro_interno_servidor(e):
    return render_template("500.html"), 500

@app.route('/health')
@app.route('/ping')
def health_check():
    return jsonify({"status": "ok", "timestamp": time.time()}), 200

@app.route('/favicon.ico')
def favicon():
    return "", 204

# ── Rotas ─────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/conversor")
def conversor_page():
    return render_template("index.html")

@app.route("/ferramentas-pdf")
def redirect_ferramentas():
    return redirect(url_for("ferramentas_pdf_page"))

@app.route("/ferramentas-avancadas")
def ferramentas_pdf_page():
    return render_template("pdf_tools.html")


@app.route("/historico")
def historico_page():
    return render_template("historico.html")


@app.route("/api/historico/restaurar/<job_id>", methods=["POST"])
def api_restaurar_historico(job_id):
    """Restaura a retenção de um arquivo no histórico enviado para 5min ou 15min."""
    if not validar_csrf():
        return jsonify({"erro": "Token CSRF inválido ou ausente."}), 403

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


@app.route("/api/historico/set-politica", methods=["POST"])
def api_set_politica():
    if not validar_csrf():
        return jsonify({"erro": "Token CSRF inválido ou ausente."}), 403

    politica = request.json.get("politica") if request.is_json else request.form.get("politica")
    politica = (politica or "15min").strip().lower()
    if politica not in ("instant", "5min", "15min"):
        politica = "15min"
    session["prisma_retention_policy"] = politica
    session.modified = True
    resp = jsonify({"ok": True, "politica": politica, "mensagem": f"Política de retenção alterada para: {politica.upper()}"})
    resp.set_cookie("prisma_retention_policy", politica, max_age=31536000, samesite="Lax")
    return resp


@app.route("/api/historico/set-seguranca", methods=["POST"])
def api_set_seguranca_historico():
    if not validar_csrf():
        return jsonify({"erro": "Token CSRF inválido ou ausente."}), 403
    payload = request.get_json(silent=True) or {}
    modo_seguro = bool(payload.get("modo_seguro", True))
    session["prisma_secure_wipe"] = modo_seguro
    session.modified = True
    return jsonify({"ok": True, "modo_seguro": modo_seguro})


@app.route("/api/historico/alterar-modo/<job_id>", methods=["POST"])
def api_alterar_modo_historico(job_id):
    if not validar_csrf():
        return jsonify({"erro": "Token CSRF inválido ou ausente."}), 403
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


@app.route("/api/historico/zip-todos", methods=["GET"])
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

    zip_filename = f"prisma_batch_{uuid.uuid4().hex[:8]}.zip"
    zip_path = os.path.join(DOWNLOAD_FOLDER, zip_filename)

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


@app.route("/api/historico/destruir-tudo", methods=["POST"])
def api_historico_destruir_tudo():
    if not validar_csrf():
        return jsonify({"erro": "Token CSRF inválido ou ausente."}), 403
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





def registrar_saida_historico(saida_path, nome_download, origem_fmt, destino_fmt, tamanho_orig=None, pasta_uid=None):
    """Registra qualquer arquivo gerado por ferramentas no histórico da sessão e no job_store."""
    job_id = uuid.uuid4().hex
    autodestruicao = session.get("prisma_retention_policy", "15min")
    if autodestruicao not in ("instant", "5min", "15min"):
        autodestruicao = "15min"

    p_uid = pasta_uid or session.get("pasta_upload", "tool")
    job_store.criar(
        job_id=job_id,
        pasta_uid=p_uid,
        nome_download=nome_download,
        autodestruicao=autodestruicao,
        origem=origem_fmt.upper(),
        destino=destino_fmt.upper(),
        tamanho_original=tamanho_orig
    )
    job_store.atualizar(job_id, caminho_saida=saida_path, concluido=True)

    if "historico" not in session:
        session["historico"] = []

    agora = time.time()
    expira_em = None
    if autodestruicao == "5min":
        expira_em = int(agora + 300)
    elif autodestruicao == "15min":
        expira_em = int(agora + 900)

    novo_item = {
        "job_id": job_id,
        "nome": nome_download,
        "origem": origem_fmt.upper(),
        "destino": destino_fmt.upper(),
        "hora": datetime.now().strftime("%H:%M"),
        "autodestruicao": autodestruicao,
        "expira_em": expira_em,
        "caminho_saida": saida_path,
        "tamanho_original": tamanho_orig,
        "apagado": False,
        "baixado": False,
        "download_url": f"/api/converter/download/{job_id}",
    }
    session["historico"].insert(0, novo_item)
    session["historico"] = session["historico"][:15]
    session.modified = True

    with _lock_contador:
        global contador_conversoes
        contador_conversoes += 1

    return job_id


def _limpar_pasta_upload(pp):
    @after_this_request
    def _cleanup(response):
        shutil.rmtree(pp, ignore_errors=True)
        return response


@app.route("/api/pdf/mesclar", methods=["POST"])
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
        job_id = registrar_saida_historico(saida, "Prisma_Mesclado.pdf", "PDF", "PDF", pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Mesclado.pdf")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_mesclar error: {e}")
        return render_template("pdf_tools.html", erro=_erro_seguro(e)), 400

@app.route("/api/pdf/dividir", methods=["POST"])
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
        job_id = registrar_saida_historico(saida, "Prisma_Dividido.zip", "PDF", "ZIP", pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Dividido.zip")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_dividir error: {e}")
        return render_template("pdf_tools.html", erro=_erro_seguro(e)), 400

@app.route("/api/pdf/proteger", methods=["POST"])
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
        job_id = registrar_saida_historico(saida, "Prisma_Protegido.pdf", "PDF", "PDF", pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Protegido.pdf")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_proteger error: {e}")
        return render_template("pdf_tools.html", erro=_erro_seguro(e)), 400

@app.route("/api/pdf/desproteger", methods=["POST"])
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
        job_id = registrar_saida_historico(saida, "Prisma_Desprotegido.pdf", "PDF", "PDF", pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Desprotegido.pdf")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_desproteger error: {e}")
        return render_template("pdf_tools.html", erro=_erro_seguro(e)), 400


@app.route("/api/pdf/comprimir", methods=["POST"])
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
        job_id = registrar_saida_historico(saida, "Prisma_Comprimido.pdf", "PDF", "PDF", tamanho_orig=sz_orig, pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Comprimido.pdf")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_comprimir error: {e}")
        return render_template("pdf_tools.html", erro=_erro_seguro(e)), 400

@app.route("/api/pdf/marca-dagua", methods=["POST"])
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
        job_id = registrar_saida_historico(saida, "Prisma_Marcado.pdf", "PDF", "PDF", pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Marcado.pdf")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_marca_dagua error: {e}")
        return render_template("pdf_tools.html", erro=_erro_seguro(e)), 400

@app.route("/api/pdf/extrair-imagens", methods=["POST"])
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
        job_id = registrar_saida_historico(saida, "Prisma_Imagens_PDF.zip", "PDF", "ZIP", pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Imagens_PDF.zip")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_extrair_imagens error: {e}")
        return render_template("pdf_tools.html", erro=_erro_seguro(e)), 400

@app.route("/api/pdf/manipular-paginas", methods=["POST"])
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
        job_id = registrar_saida_historico(saida, "Prisma_Paginas_Manipuladas.pdf", "PDF", "PDF", pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Paginas_Manipuladas.pdf")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_manipular_paginas error: {e}")
        return render_template("pdf_tools.html", erro=_erro_seguro(e)), 400

@app.route("/api/media/mp4-para-mp3", methods=["POST"])
@rate_limit_required
def api_mp4_para_mp3():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    f = request.files.get("arquivo")
    if not f or not f.filename:
        return render_template("pdf_tools.html", erro="Selecione um arquivo de vídeo MP4."), 400
    
    bitrate = request.form.get("bitrate", "192k")
    if bitrate not in ("128k", "192k", "320k"):
        bitrate = "192k"
    
    uid = criar_pasta()
    pp = pasta_path(uid)
    nome_seguro = secure_filename(f.filename) or "video.mp4"
    entrada = os.path.join(pp, nome_seguro)
    f.save(entrada)
    
    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_Audio.mp3")
    try:
        from core.media_tools import mp4_para_mp3
        mp4_para_mp3(entrada, saida, bitrate=bitrate)
        sz_orig = os.path.getsize(entrada) if os.path.exists(entrada) else None
        job_id = registrar_saida_historico(saida, "Prisma_Audio.mp3", "MP4", "MP3", tamanho_orig=sz_orig, pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Audio.mp3")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_mp4_para_mp3 error: {e}")
        return render_template("pdf_tools.html", erro=_erro_seguro(e)), 400

@app.route("/api/media/mp4-para-gif", methods=["POST"])
@rate_limit_required
def api_mp4_para_gif():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    f = request.files.get("arquivo")
    if not f or not f.filename:
        return render_template("pdf_tools.html", erro="Selecione um arquivo de vídeo MP4."), 400
    
    try:
        fps = int(request.form.get("fps", 15))
        if fps not in (10, 15, 20):
            fps = 15
    except (ValueError, TypeError):
        fps = 15

    try:
        largura = int(request.form.get("largura", 480))
        if largura not in (320, 480, 640, 0):
            largura = 480
    except (ValueError, TypeError):
        largura = 480

    uid = criar_pasta()
    pp = pasta_path(uid)
    nome_seguro = secure_filename(f.filename) or "video.mp4"
    entrada = os.path.join(pp, nome_seguro)
    f.save(entrada)
    
    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_Prisma_Animacao.gif")
    try:
        from core.media_tools import mp4_para_gif
        mp4_para_gif(entrada, saida, fps=fps, largura=largura)
        sz_orig = os.path.getsize(entrada) if os.path.exists(entrada) else None
        job_id = registrar_saida_historico(saida, "Prisma_Animacao.gif", "MP4", "GIF", tamanho_orig=sz_orig, pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Animacao.gif")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_mp4_para_gif error: {e}")
        return render_template("pdf_tools.html", erro=_erro_seguro(e)), 400




@app.route("/api/qr/gerar", methods=["POST"])
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
        from core.qr_tools import gerar_qrcode
        gerar_qrcode(texto, saida, cor_frente=cor_frente, cor_fundo=cor_fundo)
        job_id = registrar_saida_historico(saida, "Prisma_QRCode.png", "TXT", "PNG", pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_QRCode.png")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_gerar_qr error: {e}")
        return render_template("pdf_tools.html", erro=_erro_seguro(e)), 400

@app.route("/api/qr/ler", methods=["POST"])
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
        from core.qr_tools import ler_qrcode
        resultados = ler_qrcode(entrada)
        return jsonify({"codigos": resultados})
    except Exception as e:
        log.warning(f"api_ler_qr error: {e}")
        return jsonify({"erro": _erro_seguro(e)}), 400
    finally:
        shutil.rmtree(pp, ignore_errors=True)

@app.route("/api/img/paleta", methods=["POST"])
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
        from core.image_tools import extrair_paleta
        paleta = extrair_paleta(entrada, n_cores=n_cores)
        return jsonify({"paleta": paleta})
    except Exception as e:
        log.warning(f"api_paleta_cores error: {e}")
        return jsonify({"erro": _erro_seguro(e)}), 400
    finally:
        shutil.rmtree(pp, ignore_errors=True)




# ── Rotas: Modificar Arquivos ─────────────────────────────────────

@app.route("/modificar-arquivos")
def modificar_arquivos_page():
    return render_template("file_tools.html")

@app.route("/api/file/comprimir", methods=["POST"])
@rate_limit_required
def api_comprimir_arquivos():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("file_tools.html", erro="Token inválido. Recarregue a página."), 403

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
        from core.file_tools import comprimir_arquivos
        comprimir_arquivos(caminhos, saida, formato=formato)
        job_id = registrar_saida_historico(saida, f"Prisma_Comprimido.{ext_saida}", "FILE", ext_saida.upper(), pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name=f"Prisma_Comprimido.{ext_saida}")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_comprimir_arquivos error: {e}")
        return render_template("file_tools.html", erro=_erro_seguro(e)), 400

@app.route("/api/file/zip-senha", methods=["POST"])
@rate_limit_required
def api_zip_senha():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("file_tools.html", erro="Token inválido. Recarregue a página."), 403

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
        from core.file_tools import zip_com_senha
        zip_com_senha(caminhos, saida, senha)
        job_id = registrar_saida_historico(saida, "Prisma_Protegido.zip", "FILE", "ZIP", pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Protegido.zip")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_zip_senha error: {e}")
        return render_template("file_tools.html", erro=_erro_seguro(e)), 400

@app.route("/api/file/criptografar", methods=["POST"])
@rate_limit_required
def api_criptografar():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("file_tools.html", erro="Token inválido. Recarregue a página."), 403

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
        from core.file_tools import criptografar_arquivo
        criptografar_arquivo(entrada, saida, senha)
        sz_orig = os.path.getsize(entrada) if os.path.exists(entrada) else None
        job_id = registrar_saida_historico(saida, f"Prisma_{nome_seguro}.enc", "FILE", "ENC", tamanho_orig=sz_orig, pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name=f"Prisma_{nome_seguro}.enc")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_criptografar error: {e}")
        return render_template("file_tools.html", erro=_erro_seguro(e)), 400

@app.route("/api/file/descriptografar", methods=["POST"])
@rate_limit_required
def api_descriptografar():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("file_tools.html", erro="Token inválido. Recarregue a página."), 403

    f = request.files.get("arquivo")
    senha = request.form.get("senha", "")
    nome_original = request.form.get("nome_original", "arquivo_descriptografado")
    if not f: return "Selecione um arquivo", 400
    if not senha: return "A senha é obrigatória", 400
    
    uid = criar_pasta()
    pp = pasta_path(uid)
    nome_seguro = secure_filename(f.filename)
    entrada = os.path.join(pp, nome_seguro)
    f.save(entrada)
    
    # Remover .enc do nome para restaurar o original
    nome_dl = nome_seguro
    if nome_dl.endswith(".enc"):
        nome_dl = nome_dl[:-4]
    else:
        nome_dl = f"descriptografado_{nome_dl}"
    
    saida = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_{nome_dl}")
    try:
        from core.file_tools import descriptografar_arquivo
        descriptografar_arquivo(entrada, saida, senha)
        sz_orig = os.path.getsize(entrada) if os.path.exists(entrada) else None
        job_id = registrar_saida_historico(saida, nome_dl, "ENC", "FILE", tamanho_orig=sz_orig, pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name=nome_dl)
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_descriptografar error: {e}")
        return render_template("file_tools.html", erro=_erro_seguro(e)), 400

@app.route("/api/file/hash", methods=["POST"])
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
        from core.file_tools import calcular_hashes
        hashes = calcular_hashes(entrada)
        hashes["nome"] = f.filename
        return jsonify(hashes)
    except Exception as e:
        log.warning(f"api_calcular_hash error: {e}")
        return jsonify({"erro": _erro_seguro(e)}), 400
    finally:
        shutil.rmtree(pp, ignore_errors=True)

@app.route("/api/file/renomear-lote", methods=["POST"])
@rate_limit_required
def api_renomear_lote():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("file_tools.html", erro="Token inválido. Recarregue a página."), 403

    arquivos = request.files.getlist("arquivos")
    # SEC-PATH: sanitiza o padrão de nome para prevenir Path Traversal.
    # Permite apenas: letras, números, underscore, hífen, espaço e o token {n}.
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
        from core.file_tools import renomear_em_lote
        renomear_em_lote(caminhos, padrao, saida)
        job_id = registrar_saida_historico(saida, "Prisma_Renomeados.zip", "FILE", "ZIP", pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name="Prisma_Renomeados.zip")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_renomear_lote error: {e}")
        return render_template("file_tools.html", erro=_erro_seguro(e)), 400

@app.route("/api/data/mesclar-planilhas", methods=["POST"])
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
        job_id = registrar_saida_historico(saida, f"Prisma_Planilhas_Mescladas.{formato}", "XLSX", formato.upper(), pasta_uid=uid)
        _limpar_pasta_upload(pp)
        resp = send_file(saida, as_attachment=True, download_name=f"Prisma_Planilhas_Mescladas.{formato}")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        log.warning(f"api_mesclar_planilhas error: {e}")
        return render_template("pdf_tools.html", erro=_erro_seguro(e)), 400

@app.route("/manifest.json")
def serve_manifest():
    return send_file("static/manifest.json", mimetype="application/manifest+json")

@app.route("/sw.js")
def serve_sw():
    return send_file("static/sw.js", mimetype="application/javascript")

_lock_build_desktop = Lock()

@app.route("/download-app")
def download_app():
    possiveis_caminhos = [
        os.path.join("dist", "Prisma.exe"),
        os.path.join("dist", "Prisma", "Prisma.exe"),
        os.path.join("dist", "Prisma-Setup.exe"),
        os.path.join("dist", "Prisma_Desktop.zip")
    ]
    for caminho in possiveis_caminhos:
        if os.path.exists(caminho):
            return send_file(caminho, as_attachment=True, download_name=os.path.basename(caminho))

    # Redirecionamento seguro para a release oficial (evita PyInstaller em runtime via HTTP DoS)
    release_url = os.environ.get("GITHUB_RELEASE_URL", "https://github.com/GuGoulart/Prisma-Converter/releases/latest/download/Prisma.exe")
    return redirect(release_url)

@app.route("/download-apk")
def download_apk():
    possiveis_apk = [
        os.path.join("dist", "Prisma.apk"),
        os.path.join("static", "Prisma.apk"),
        "Prisma.apk"
    ]
    for apk_path in possiveis_apk:
        if os.path.exists(apk_path):
            return send_file(apk_path, as_attachment=True, download_name="Prisma.apk", mimetype="application/vnd.android.package-archive")

    github_apk_url = os.environ.get("GITHUB_APK_URL", "https://github.com/GuGoulart/Prisma-Converter/releases/latest/download/Prisma.apk")
    return redirect(github_apk_url)


@app.route("/preview/<pasta_uuid>/<preview_file>")
def preview_arquivo(pasta_uuid, preview_file):
    # AUD-007: valida formato UUID (hex 32 chars) para defesa em profundidade
    if not re.match(r'^[a-f0-9]{32}$', pasta_uuid):
        abort(400)
    if session.get("pasta_upload") != pasta_uuid:
        abort(403)
    if not re.match(r'^[a-zA-Z0-9_]+\.[a-zA-Z0-9]{1,10}$', preview_file):
        abort(400)
    c = os.path.join(UPLOAD_FOLDER, pasta_uuid, preview_file)
    if not os.path.exists(c):
        abort(404)
    return send_file(c)


@app.route("/preview-convert/<pasta_uuid>/<destino>")
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

    extensao     = session.get("arquivo_ext", "")
    arquivo_nome = session.get("arquivo_nome", "")
    pp           = pasta_path(pasta_uuid)
    entrada      = os.path.join(pp, arquivo_nome)

    if not os.path.exists(entrada):
        abort(404)
    if extensao == destino:
        return send_file(entrada)

    ori_key   = f"_{orientacao}" if destino == "pdf" else ""
    prev_nome = f"prev_{destino}{ori_key}.{destino}"
    prev_path = os.path.join(pp, prev_nome)

    if not os.path.exists(prev_path):
        err = [None]; done = threading.Event()
        def _g():
            try:
                converter_arquivo(entrada, prev_path, extensao, destino,
                                  orientacao=orientacao)
            except Exception as e:
                err[0] = e
            finally:
                done.set()
        threading.Thread(target=_g, daemon=True).start()
        done.wait(timeout=TIMEOUT_PREVIEW)
        if not done.is_set():
            abort(504)
        if err[0] or not os.path.exists(prev_path):
            abort(500, description=_erro_seguro(err[0]) if err[0] else "Erro ao gerar prévia")

    return send_file(prev_path)


@app.route("/preview-tabela/<pasta_uuid>/<destino>")
def preview_tabela(pasta_uuid, destino):
    if not re.match(r'^[a-f0-9]{32}$', pasta_uuid):
        abort(400)
    if session.get("pasta_upload") != pasta_uuid:
        abort(403)
    if destino not in ("csv", "xlsx", "json"):
        abort(400)

    extensao     = session.get("arquivo_ext", "")
    arquivo_nome = session.get("arquivo_nome", "")
    pp           = pasta_path(pasta_uuid)
    entrada      = os.path.join(pp, arquivo_nome)

    if not os.path.exists(entrada):
        abort(404)

    # Sempre mostra os dados reais do arquivo original
    # Se o arquivo já é CSV/XLSX/JSON, lê direto; senão converte
    if extensao in ("csv", "xlsx", "xls", "json"):
        alvo     = entrada
        alvo_ext = extensao
    else:
        # Converte para o destino pedido e mostra
        cache = os.path.join(pp, f"prev_{destino}.{destino}")
        if not os.path.exists(cache):
            try:
                converter_arquivo(entrada, cache, extensao, destino)
            except Exception as e:
                # AUD-004: usa _erro_seguro para não expor detalhes internos
                return Response(
                    f"<p class='prev-erro-msg'>Erro ao converter: {_erro_seguro(e)}</p>",
                    status=500
                )
        alvo     = cache
        alvo_ext = destino

    # Limite máximo de 100 linhas para não travar a memória/navegador
    tabela = gerar_preview_tabela(alvo, alvo_ext, limite=100)

    if tabela:
        return Response(tabela, content_type="text/html")
    return Response(
        "<p class='prev-erro-msg'>Não foi possível gerar a tabela.</p>",
        status=500
    )


@app.route("/upload", methods=["POST"])
def upload():
    global contador_conversoes
    ip = extrair_ip_cliente(request)

    if not verificar_rate_limit(ip):
        return render_template("index.html", erro="Muitas requisições. Aguarde um momento.")
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

        # SEC-MIME: valida Content-Type HTTP — defesa complementar ao magic bytes
        if not validar_mime_type(arq, {ext}):
            return render_template("index.html", erro="Tipo de arquivo não permitido.")

        conteudo = arq.read()
        tamanho  = len(conteudo)

        limite = LIMITES_POR_TIPO.get(ext, MAX_MB * 1024 * 1024)
        if tamanho > limite:
            return render_template("index.html",
                erro=f"Arquivo muito grande para '{ext.upper()}'. Limite: {NOMES_LIMITES.get(ext, f'{MAX_MB} MB')}.")

        uid    = criar_pasta()
        pp     = pasta_path(uid)
        nome_i = f"arquivo.{ext}"
        cam    = os.path.join(pp, nome_i)

        with open(cam, "wb") as f:
            f.write(conteudo)

        if not validar_magic(cam, ext):
            shutil.rmtree(pp, ignore_errors=True)
            return render_template("index.html",
                                   erro=f"Arquivo não parece ser '{ext.upper()}' válido.")

        # SEC-ZIPBOMB: verifica se é uma Zip Bomb antes de qualquer extração
        if ext in ("zip",) and not verificar_zip_bomb(cam):
            shutil.rmtree(pp, ignore_errors=True)
            return render_template("index.html",
                                   erro="Arquivo ZIP suspeito: tamanho descomprimido excede o limite permitido.")

        conversoes = obter_conversoes(ext)
        if not conversoes:
            shutil.rmtree(pp, ignore_errors=True)
            return render_template("index.html",
                                   erro=f"Formato '.{ext}' não suportado.")

        session["pasta_upload"] = uid
        session["arquivo_nome"] = nome_i
        session["arquivo_ext"]  = ext
        session.modified = True
        log.info(f"Upload OK: {nome_original} ({tamanho}b) — {ip}")

        # ── Preview inicial ──────────────────────────────────────
        preview_url  = None
        preview_tipo = None
        tabela_html  = None

        if ext == "pdf":
            preview_url  = f"/preview/{uid}/{nome_i}"
            preview_tipo = "pdf"

        elif ext in ("png", "jpg", "jpeg", "webp", "heic"):
            preview_url  = f"/preview/{uid}/{nome_i}"
            preview_tipo = "imagem"

        elif ext in ("csv", "xlsx", "xls", "json"):
            # PERF-003: limite=500 evita OOM com arquivos CSV muito grandes
            tabela_html = gerar_preview_tabela(cam, ext, limite=500)

        else:
            # DOCX/PPT/PPTX: tenta gerar PDF de prévia em background
            prev_p = os.path.join(pp, "preview_source.pdf")
            err = [None]; done = threading.Event()
            def _p():
                try: converter_arquivo(cam, prev_p, ext, "pdf")
                except Exception as e: err[0] = e
                finally: done.set()
            threading.Thread(target=_p, daemon=True).start()
            done.wait(timeout=30)
            if not err[0] and os.path.exists(prev_p):
                preview_url  = f"/preview/{uid}/preview_source.pdf"
                preview_tipo = "pdf"

        return render_template("index.html",
            arquivo=nome_i,
            nome_original=nome_original,
            origem=ext,
            conversoes=conversoes,
            preview_url=preview_url,
            preview_tipo=preview_tipo,
            tabela_html=tabela_html,
        )

    except Exception as e:
        log.error(f"Upload error — {ip} — {traceback.format_exc()}")
        # AUD-003: usa _erro_seguro em vez de str(e) para não expor detalhes internos
        return render_template("index.html", erro=_erro_seguro(e))


@app.route("/converter", methods=["POST"])
def converter():
    global _conversoes_ativas
    global contador_conversoes
    ip = extrair_ip_cliente(request)

    if not verificar_rate_limit(ip):
        return render_template("index.html", erro="Muitas requisições.")
    if not validar_csrf(request.form.get("csrf_token", "")):
        return render_template("index.html", erro="Token inválido.")

    with _lock_conv:
        if _conversoes_ativas >= MAX_PARALELAS:
            return render_template("index.html",
                                   erro="Servidor ocupado. Tente em instantes.")
        _conversoes_ativas += 1

    uid            = session.get("pasta_upload", "")
    arquivo_nome   = session.get("arquivo_nome", "")
    origem         = request.form.get("origem", "")
    destino        = request.form.get("destino", "")
    nome_original  = request.form.get("nome_original", "arquivo")
    download_token = request.form.get("downloadToken", "")
    orientacao     = request.form.get("orientacao", "retrato")
    if orientacao not in ("retrato", "paisagem"):
        orientacao = "retrato"

    if not re.match(r'^[a-f0-9]{32}$', uid):
        with _lock_conv: _conversoes_ativas -= 1
        return render_template("index.html", erro="Sessão inválida.")

    pp      = pasta_path(uid)
    entrada = os.path.join(pp, arquivo_nome)
    if not os.path.exists(entrada):
        with _lock_conv: _conversoes_ativas -= 1
        return render_template("index.html",
                               erro="Arquivo expirou. Envie novamente.")

    saida = None
    try:
        base       = re.sub(r'[^\w\-_. ]', '_',
                            os.path.splitext(secure_filename(nome_original))[0]).strip() or "arquivo"
        
        if destino in ("png", "jpg", "jpeg", "webp", "heic") and origem not in ("png", "jpg", "jpeg", "webp", "heic"):
            nome_saida = f"{base}_{destino.upper()}s.zip"
        else:
            nome_saida = f"{base}.{destino}"
            
        saida      = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_{nome_saida}")

        err = [None]; done = threading.Event()
        def _c():
            try:
                converter_arquivo(entrada, saida, origem, destino,
                                  orientacao=orientacao)
            except Exception as e:
                err[0] = e
            finally:
                done.set()
        threading.Thread(target=_c, daemon=True).start()
        done.wait(timeout=TIMEOUT_CONV)

        if not done.is_set():
            return render_template("index.html",
                                   erro="Tempo excedido. Tente com um arquivo menor.")
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

        # QC-005: usa lock para incremento thread-safe do contador
        with _lock_contador:
            contador_conversoes += 1
        log.info(f"OK: {nome_original} | {origem.upper()}->{destino.upper()} | {ip}")

        if "historico" not in session:
            session["historico"] = []
        session["historico"].insert(0, {
            "nome":    nome_original,
            "origem":  origem.upper(),
            "destino": destino.upper(),
            "hora":    datetime.now().strftime("%H:%M"),
        })
        session["historico"]    = session["historico"][:5]
        session["pasta_upload"] = ""
        session.modified = True

        resp = send_file(saida, as_attachment=True, download_name=nome_saida)
        resp.headers["Cache-Control"] = "no-store"  # DL-002
        if download_token:
            # SEG-011: Secure=True em produção (PORT definida = Cloud Run)
            is_secure = bool(os.environ.get("PORT"))
            resp.set_cookie("downloadToken", download_token,
                            max_age=60, samesite="Lax", secure=is_secure)
        return resp

    except Exception as e:
        log.error(f"Conversão error — {traceback.format_exc()}")
        try: shutil.rmtree(pp, ignore_errors=True)
        except Exception: pass
        return render_template("index.html", erro=_erro_seguro(e))
    finally:
        with _lock_conv:
            _conversoes_ativas -= 1


# ── API de Conversão Assíncrona ───────────────────────────────────────────────────────
#
# Fluxo:
#   1. POST /api/converter/async — inicia job, retorna {job_id}
#   2. GET  /api/converter/status/<job_id> — retorna progresso (percent, status, concluido)
#   3. GET  /api/converter/download/<job_id> — retorna o arquivo quando concluido=True
#
# O frontend faz polling do endpoint de status e inicia o download automaticamente.
# Esta arquitetura elimina a espera síncrona de até 120s na rota /converter.

@app.route("/api/converter/async", methods=["POST"])
@rate_limit_required
def api_converter_async():
    """Inicia uma conversão assíncrona e retorna um job_id para polling."""
    global _conversoes_ativas
    if not validar_csrf(request.form.get("csrf_token", "")):
        return jsonify({"erro": "Token inválido. Recarregue a página."}), 403

    uid            = session.get("pasta_upload", "")
    arquivo_nome   = session.get("arquivo_nome", "")
    origem         = request.form.get("origem", "").strip().lower()
    destino        = request.form.get("destino", "").strip().lower()
    nome_original  = request.form.get("nome_original", "arquivo")
    orientacao     = request.form.get("orientacao", "retrato")
    autodestruicao = (request.form.get("autodestruicao") or session.get("prisma_retention_policy") or request.cookies.get("prisma_retention_policy", "15min")).strip().lower()

    if orientacao not in ("retrato", "paisagem"):
        orientacao = "retrato"
    if autodestruicao not in ("instant", "5min", "15min"):
        autodestruicao = "15min"

    # Validar sessão e arquivo
    if not re.match(r'^[a-f0-9]{32}$', uid):
        return jsonify({"erro": "Sessão inválida. Faça o upload novamente."}), 400
    if not origem or not destino:
        return jsonify({"erro": "Formato de origem ou destino não especificado."}), 400

    pp      = pasta_path(uid)
    entrada = os.path.join(pp, arquivo_nome)
    if not os.path.exists(entrada):
        return jsonify({"erro": "Arquivo expirou. Faça o upload novamente."}), 400

    # Verificar limite de conversões paralelas
    with _lock_conv:
        if _conversoes_ativas >= MAX_PARALELAS:
            return jsonify({"erro": "Servidor ocupado. Aguarde um momento e tente novamente."}), 503
        _conversoes_ativas += 1

    try:
        base = re.sub(r'[^\w\-_. ]', '_',
                      os.path.splitext(secure_filename(nome_original))[0]).strip() or "arquivo"
        if destino in ("png", "jpg", "jpeg", "webp", "heic") and \
           origem not in ("png", "jpg", "jpeg", "webp", "heic"):
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

        log.info("[async] Job %s iniciado: %s->%s (%s) [Autodestruição: %s]", job_id[:8], origem, destino, nome_original, autodestruicao)
        return jsonify({"ok": True, "job_id": job_id})

    except Exception as e:
        with _lock_conv:
            _conversoes_ativas -= 1
        log.error("[async] Erro ao iniciar job: %s", e)
        return jsonify({"erro": _erro_seguro(e)}), 500


@app.route("/api/converter/status/<job_id>", methods=["GET"])
def api_converter_status(job_id):
    """Retorna o progresso e status de um job de conversão assíncrona."""
    if not re.match(r'^[a-f0-9]{32}$', job_id):
        return jsonify({"erro": "Job ID inválido."}), 400

    job = job_store.get(job_id)
    if not job:
        return jsonify({"erro": "Job não encontrado ou expirado."}), 404

    return jsonify({
        "percent":   job["percent"],
        "status":    job["status"],
        "concluido": job["concluido"],
        "erro":      job["erro"],
        "download_url": f"/api/converter/download/{job_id}" if job["concluido"] and not job["erro"] else None,
    })


@app.route("/api/converter/download/<job_id>", methods=["GET"])
def api_converter_download(job_id):
    """Retorna o arquivo convertido quando a conversão estiver concluída."""
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

    saida          = job["caminho_saida"]
    nome_download  = job["nome_download"]
    pasta_uid      = job["pasta_uid"]
    autodestruicao = job.get("autodestruicao", "15min")

    # Verificar se o arquivo ainda existe (pode ter sido limpo)
    if not storage.existe(saida):
        job_store.remover(job_id)
        return render_template("index.html", erro="O arquivo convertido expirou. Faça o processo novamente."), 404

    # Atualizar histórico da sessão com metadados ricos e timestamp de expiração
    if "historico" not in session:
        session["historico"] = []

    ext_destino = nome_download.rsplit(".", 1)[-1].upper() if "." in nome_download else "?"
    ext_origem  = job.get("origem", "?").upper()
    timestamp_job = job.get("timestamp", time.time())

    expira_em = None
    if autodestruicao == "5min":
        expira_em = int(timestamp_job + 300)
    elif autodestruicao == "15min":
        expira_em = int(timestamp_job + 900)

    apagado_agora = (autodestruicao == "instant")

    # Procura se o job já consta no histórico para atualizar seu estado
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
            "job_id":        job_id,
            "nome":          nome_download,
            "origem":        ext_origem,
            "destino":       ext_destino,
            "hora":          datetime.now().strftime("%H:%M"),
            "autodestruicao": autodestruicao,
            "expira_em":     expira_em,
            "caminho_saida": saida,
            "apagado":       apagado_agora,
            "baixado":       True,
            "download_url":  f"/api/converter/download/{job_id}",
        }
        session["historico"].insert(0, novo_item)
        session["historico"] = session["historico"][:8]

    session["pasta_upload"] = ""
    session.modified = True

    # Se a política for 'instant' (Autodestruição Instantânea), remove do job_store e limpa o disco logo após o envio
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
        # Se for 5min ou 15min, libera o lock de conversão ativa após envio
        @after_this_request
        def cleanup_lazy(response):
            with _lock_conv:
                global _conversoes_ativas
                _conversoes_ativas = max(0, _conversoes_ativas - 1)
            return response

    # Atualizar contador de conversões
    with _lock_contador:
        global contador_conversoes
        contador_conversoes += 1

    copiar_para_downloads_desktop(saida, nome_download)
    resp = send_file(saida, as_attachment=True, download_name=nome_download)
    resp.headers["Cache-Control"] = "no-store"
    return resp


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG") == "1"
    app.run(debug=debug_mode, host="0.0.0.0", port=port)