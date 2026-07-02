from flask import Flask, render_template, request, send_file, session, after_this_request
from converter import obter_conversoes, converter_arquivo, obter_motor
from werkzeug.utils import secure_filename
from datetime import datetime
from collections import defaultdict
from threading import Lock
from dotenv import load_dotenv

import os
import re
import secrets
import shutil
import time
import uuid
import logging
import threading
import traceback
import pandas as pd

# ─────────────────────────────────────────
# Carrega variáveis do .env
# ─────────────────────────────────────────

load_dotenv()

# ─────────────────────────────────────────
# App
# ─────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-local-key")

UPLOAD_FOLDER   = "uploads"
DOWNLOAD_FOLDER = "downloads"
MAX_MB          = 50
TIMEOUT_CONV    = 120

app.config["UPLOAD_FOLDER"]      = UPLOAD_FOLDER
app.config["DOWNLOAD_FOLDER"]    = DOWNLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024

os.makedirs(UPLOAD_FOLDER,   exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

contador_conversoes = 0

# ─────────────────────────────────────────
# Logging estruturado em arquivo
# ─────────────────────────────────────────

logging.basicConfig(
    filename="prisma.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────
# Cabeçalhos de segurança HTTP
# ─────────────────────────────────────────

@app.after_request
def cabecalhos_seguranca(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]         = "DENY"
    response.headers["X-XSS-Protection"]        = "1; mode=block"
    response.headers["Referrer-Policy"]          = "no-referrer"
    return response

# ─────────────────────────────────────────
# Rate limiting
# ─────────────────────────────────────────

_contagem_ip = defaultdict(list)
_lock_rate   = Lock()
RATE_LIMITE  = 10
RATE_JANELA  = 60  # segundos


def verificar_rate_limit(ip: str) -> bool:
    agora = time.time()
    with _lock_rate:
        _contagem_ip[ip] = [t for t in _contagem_ip[ip] if agora - t < RATE_JANELA]
        if len(_contagem_ip[ip]) >= RATE_LIMITE:
            return False
        _contagem_ip[ip].append(agora)
        return True

# ─────────────────────────────────────────
# Limite de conversões paralelas
# ─────────────────────────────────────────

_conversoes_ativas = 0
_lock_conv         = Lock()
MAX_PARALELAS      = 3

# ─────────────────────────────────────────
# CSRF
# ─────────────────────────────────────────

def gerar_csrf() -> str:
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def validar_csrf(token_form: str) -> bool:
    return bool(token_form and token_form == session.get("csrf_token"))

# ─────────────────────────────────────────
# Limite de tamanho por tipo de arquivo
# ─────────────────────────────────────────

LIMITES_POR_TIPO = {
    "csv":   5 * 1024 * 1024,
    "xlsx": 20 * 1024 * 1024,
    "xls":  20 * 1024 * 1024,
    "pdf":  50 * 1024 * 1024,
    "docx": 20 * 1024 * 1024,
    "doc":  20 * 1024 * 1024,
    "ppt":  50 * 1024 * 1024,
    "pptx": 50 * 1024 * 1024,
    "png":  10 * 1024 * 1024,
    "jpg":  10 * 1024 * 1024,
    "jpeg": 10 * 1024 * 1024,
}

NOMES_LIMITES = {k: f"{v // (1024 * 1024)} MB" for k, v in LIMITES_POR_TIPO.items()}

# ─────────────────────────────────────────
# Validação de extensões duplas perigosas
# ─────────────────────────────────────────

_EXTENSOES_PERIGOSAS = {
    "exe", "bat", "cmd", "com", "php", "sh",
    "ps1", "vbs", "js",  "jar", "py",  "rb",
    "pl",  "asp", "jsp", "cgi", "msi", "dll",
}


def validar_nome_arquivo(nome: str) -> bool:
    partes = nome.split(".")
    if len(partes) <= 2:
        return True
    for parte in partes[1:-1]:
        if parte.lower() in _EXTENSOES_PERIGOSAS:
            return False
    return True

# ─────────────────────────────────────────
# Validação de magic bytes
# ─────────────────────────────────────────

_MAGIC = {
    "pdf":  [b"%PDF"],
    "docx": [b"PK\x03\x04"],
    "xlsx": [b"PK\x03\x04"],
    "pptx": [b"PK\x03\x04"],
    "ppt":  [b"\xd0\xcf\x11\xe0"],
    "doc":  [b"\xd0\xcf\x11\xe0"],
    "xls":  [b"\xd0\xcf\x11\xe0"],
    "png":  [b"\x89PNG"],
    "jpg":  [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "csv":  None,
}


def validar_magic_bytes(caminho: str, extensao: str) -> bool:
    magics = _MAGIC.get(extensao)
    if magics is None:
        return True
    try:
        with open(caminho, "rb") as f:
            header = f.read(8)
        return any(header.startswith(m) for m in magics)
    except Exception:
        return False

# ─────────────────────────────────────────
# Isolamento por pasta de sessão
# ─────────────────────────────────────────

def criar_pasta_sessao() -> str:
    pasta_uuid = uuid.uuid4().hex
    pasta      = os.path.join(UPLOAD_FOLDER, pasta_uuid)
    os.makedirs(pasta, exist_ok=True)
    return pasta_uuid


def pasta_sessao_path(pasta_uuid: str) -> str:
    return os.path.join(UPLOAD_FOLDER, pasta_uuid)

# ─────────────────────────────────────────
# Limpeza residual em background
# ─────────────────────────────────────────

def _limpar_residuos():
    limite = 15 * 60
    while True:
        time.sleep(900)
        agora = time.time()
        for item in os.listdir(UPLOAD_FOLDER):
            caminho = os.path.join(UPLOAD_FOLDER, item)
            try:
                if agora - os.path.getmtime(caminho) > limite:
                    if os.path.isdir(caminho):
                        shutil.rmtree(caminho, ignore_errors=True)
                    elif os.path.isfile(caminho):
                        os.remove(caminho)
            except Exception:
                pass
        for item in os.listdir(DOWNLOAD_FOLDER):
            caminho = os.path.join(DOWNLOAD_FOLDER, item)
            try:
                if os.path.isfile(caminho):
                    if agora - os.path.getmtime(caminho) > limite:
                        os.remove(caminho)
            except Exception:
                pass


threading.Thread(target=_limpar_residuos, daemon=True).start()

# ─────────────────────────────────────────
# Context processor
# ─────────────────────────────────────────

@app.context_processor
def inject_globals():
    return {
        "contador":   contador_conversoes,
        "historico":  session.get("historico", []),
        "motor":      obter_motor(),
        "csrf_token": gerar_csrf(),
    }

# ─────────────────────────────────────────
# Erros HTTP
# ─────────────────────────────────────────

@app.errorhandler(413)
def arquivo_grande(e):
    log.warning("Arquivo rejeitado: tamanho excedeu MAX_CONTENT_LENGTH")
    return render_template("index.html", erro=f"Arquivo muito grande. Limite geral: {MAX_MB} MB."), 413

# ─────────────────────────────────────────
# Preview de tabela
# ─────────────────────────────────────────

def gerar_preview(caminho: str, extensao: str):
    try:
        if extensao == "csv":
            df = pd.read_csv(caminho, nrows=5, sep=None, engine="python")
        elif extensao in ("xlsx", "xls"):
            df = pd.read_excel(caminho, nrows=5, engine="openpyxl")
        else:
            return None
        if len(df.columns) > 8:
            df = df.iloc[:, :8]
        return df.to_html(classes="tabela-preview", border=0, index=False)
    except Exception:
        return None

# ─────────────────────────────────────────
# Rota principal
# ─────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")

# ─────────────────────────────────────────
# Upload
# ─────────────────────────────────────────

@app.route("/upload", methods=["POST"])
def upload():
    ip = request.remote_addr

    if not verificar_rate_limit(ip):
        log.warning(f"Rate limit atingido — IP: {ip}")
        return render_template("index.html", erro="Muitas requisições. Aguarde um momento.")

    if not validar_csrf(request.form.get("csrf_token", "")):
        log.warning(f"CSRF inválido no upload — IP: {ip}")
        return render_template("index.html", erro="Token de segurança inválido. Recarregue a página.")

    try:
        if "arquivo" not in request.files:
            return render_template("index.html", erro="Nenhum arquivo enviado.")

        arquivo = request.files["arquivo"]

        if not arquivo or arquivo.filename == "":
            return render_template("index.html", erro="Selecione um arquivo.")

        nome_original = arquivo.filename.strip()

        if not validar_nome_arquivo(nome_original):
            log.warning(f"Extensão dupla bloqueada: {nome_original} — IP: {ip}")
            return render_template("index.html", erro="Nome de arquivo suspeito. Verifique o arquivo.")

        if "." not in nome_original:
            return render_template("index.html", erro="O arquivo não possui extensão reconhecida.")

        extensao = nome_original.rsplit(".", 1)[1].lower()

        conteudo = arquivo.read()
        tamanho  = len(conteudo)

        limite_tipo = LIMITES_POR_TIPO.get(extensao, MAX_MB * 1024 * 1024)
        if tamanho > limite_tipo:
            log.info(f"Arquivo muito grande para {extensao}: {tamanho} bytes — IP: {ip}")
            return render_template(
                "index.html",
                erro=f"Arquivo muito grande para '{extensao.upper()}'. Limite: {NOMES_LIMITES.get(extensao, f'{MAX_MB} MB')}."
            )

        pasta_uuid = criar_pasta_sessao()
        pasta_path = pasta_sessao_path(pasta_uuid)
        nome_interno = f"arquivo.{extensao}"
        caminho = os.path.join(pasta_path, nome_interno)

        with open(caminho, "wb") as f:
            f.write(conteudo)

        if not validar_magic_bytes(caminho, extensao):
            shutil.rmtree(pasta_path, ignore_errors=True)
            log.warning(f"Magic bytes inválidos: {nome_original} — IP: {ip}")
            return render_template(
                "index.html",
                erro=f"O arquivo não parece ser um '{extensao.upper()}' válido. Pode estar corrompido."
            )

        conversoes = obter_conversoes(extensao)
        if not conversoes:
            shutil.rmtree(pasta_path, ignore_errors=True)
            return render_template("index.html", erro=f"Formato '.{extensao}' ainda não é suportado.")

        session["pasta_upload"] = pasta_uuid
        session["arquivo_nome"] = nome_interno
        session["arquivo_ext"]  = extensao
        session.modified = True

        log.info(f"Upload OK: {nome_original} ({tamanho} bytes) — IP: {ip}")

        tabela_html = gerar_preview(caminho, extensao)

        return render_template(
            "index.html",
            arquivo=nome_interno,
            nome_original=nome_original,
            origem=extensao,
            conversoes=conversoes,
            tabela_html=tabela_html,
        )

    except Exception as erro:
        log.error(f"Erro no upload — IP: {ip} — {traceback.format_exc()}")
        return render_template("index.html", erro=str(erro))

# ─────────────────────────────────────────
# Conversão
# ─────────────────────────────────────────

@app.route("/converter", methods=["POST"])
def converter():
    global _conversoes_ativas, contador_conversoes

    ip = request.remote_addr

    if not verificar_rate_limit(ip):
        log.warning(f"Rate limit atingido na conversão — IP: {ip}")
        return render_template("index.html", erro="Muitas requisições. Aguarde um momento.")

    if not validar_csrf(request.form.get("csrf_token", "")):
        log.warning(f"CSRF inválido na conversão — IP: {ip}")
        return render_template("index.html", erro="Token de segurança inválido. Recarregue a página.")

    with _lock_conv:
        if _conversoes_ativas >= MAX_PARALELAS:
            return render_template("index.html", erro="Servidor ocupado. Aguarde alguns segundos e tente novamente.")
        _conversoes_ativas += 1

    pasta_uuid    = session.get("pasta_upload", "")
    arquivo_nome  = session.get("arquivo_nome", "")
    origem        = request.form.get("origem", "")
    destino       = request.form.get("destino", "")
    nome_original = request.form.get("nome_original", "arquivo")
    download_token = request.form.get("downloadToken", "")

    if not re.match(r'^[a-f0-9]{32}$', pasta_uuid):
        with _lock_conv:
            _conversoes_ativas -= 1
        return render_template("index.html", erro="Sessão inválida. Envie o arquivo novamente.")

    pasta_path = pasta_sessao_path(pasta_uuid)
    entrada    = os.path.join(pasta_path, arquivo_nome)

    if not os.path.exists(entrada):
        with _lock_conv:
            _conversoes_ativas -= 1
        return render_template("index.html", erro="Arquivo expirou. Envie novamente.")

    saida = None

    try:
        nome_base  = os.path.splitext(secure_filename(nome_original))[0]
        nome_base  = re.sub(r'[^\w\-_. ]', '_', nome_base).strip() or "arquivo"
        nome_saida = f"{nome_base}.{destino}"
        saida      = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}_{nome_saida}")

        erro_conv = [None]
        concluido = threading.Event()

        def _converter():
            try:
                converter_arquivo(entrada, saida, origem, destino)
            except Exception as e:
                erro_conv[0] = e
            finally:
                concluido.set()

        t = threading.Thread(target=_converter, daemon=True)
        t.start()
        concluido.wait(timeout=TIMEOUT_CONV)

        if not concluido.is_set():
            log.error(f"Timeout na conversão {origem}→{destino} — IP: {ip}")
            return render_template("index.html", erro="Tempo de conversão excedido. Tente um arquivo menor.")

        if erro_conv[0]:
            raise erro_conv[0]

        @after_this_request
        def deletar(response):
            try:
                shutil.rmtree(pasta_path, ignore_errors=True)
            except Exception:
                pass
            try:
                if saida and os.path.exists(saida):
                    os.remove(saida)
            except Exception:
                pass
            return response

        contador_conversoes += 1
        log.info(f"Conversão OK: {nome_original} | {origem.upper()}→{destino.upper()} | IP: {ip}")

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

        response = send_file(saida, as_attachment=True, download_name=nome_saida)

        if download_token:
            response.set_cookie("downloadToken", download_token, max_age=60, samesite="Lax")

        return response

    except Exception as erro:
        log.error(f"Erro na conversão {origem}→{destino} — IP: {ip} — {traceback.format_exc()}")
        try:
            shutil.rmtree(pasta_path, ignore_errors=True)
        except Exception:
            pass
        return render_template("index.html", erro=str(erro))

    finally:
        with _lock_conv:
            _conversoes_ativas -= 1


if __name__ == "__main__":
    app.run(debug=True)