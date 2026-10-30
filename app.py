"""app.py — Ponto de entrada do Prisma Converter (aplicativo desktop local)."""
import hashlib
import json
import logging
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, url_for

from core import config
from core.converter import CONVERSOES
from core.ffmpeg import ffmpeg_disponivel, preparar_ffmpeg
from core.jobs import jobs
from core.security import aplicar_cabecalhos, proteger_requisicao
from routes import registrar_blueprints
from routes.views import injetar_globais

load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("prisma")

PORTA_PADRAO = 5000
# Abas em segundo plano têm os timers limitados a 1/min pelo navegador.
TOLERANCIA_SEM_JANELA = int(os.environ.get("PRISMA_SHUTDOWN_SECONDS", 180))
_ultimo_sinal = {"t": 0.0}


def _versao_asset(caminho: str, cache: dict = {}) -> str:
    """Hash do conteúdo: permite cache longo sem nunca servir arquivo antigo."""
    completo = os.path.join(config.BASE_DIR, "static", caminho)
    try:
        mtime = os.path.getmtime(completo)
    except OSError:
        return "0"
    chave = (caminho, mtime)
    if chave not in cache:
        with open(completo, "rb") as f:
            cache[chave] = hashlib.sha256(f.read()).hexdigest()[:12]
    return cache[chave]


def create_app() -> Flask:
    config.garantir_pastas()
    app = Flask(__name__)
    app.secret_key = config.carregar_chave_secreta()
    app.config.update(
        MAX_CONTENT_LENGTH=config.MAX_UPLOAD_BYTES,
        MAX_FORM_MEMORY_SIZE=8 * 1024 * 1024,
        SESSION_COOKIE_SAMESITE="Strict",
        SESSION_COOKIE_HTTPONLY=True,
        SEND_FILE_MAX_AGE_DEFAULT=31536000,
    )

    app.before_request(proteger_requisicao)
    app.after_request(aplicar_cabecalhos)
    app.context_processor(lambda: {
        **injetar_globais(),
        "ffmpeg_ok": ffmpeg_disponivel(),
        "todas_conversoes": CONVERSOES,
        "asset": lambda caminho: url_for("static", filename=caminho, v=_versao_asset(caminho)),
    })
    registrar_blueprints(app)

    def _quer_json() -> bool:
        return request.path.startswith("/api/")

    @app.errorhandler(403)
    def _proibido(_e):
        return jsonify({"erro": "Acesso negado."}), 403

    @app.errorhandler(404)
    def _nao_encontrado(_e):
        return (jsonify({"erro": "Não encontrado."}), 404) if _quer_json() else (render_template("404.html"), 404)

    @app.errorhandler(413)
    def _grande(_e):
        return jsonify({"erro": "Arquivo grande demais."}), 413

    @app.errorhandler(500)
    def _interno(_e):
        return (jsonify({"erro": "Erro interno."}), 500) if _quer_json() else (render_template("500.html"), 500)

    @app.route("/api/heartbeat", methods=["POST"])
    def heartbeat():
        _ultimo_sinal["t"] = time.monotonic()
        return "", 204

    return app


app = create_app()


# ── Execução desktop ──────────────────────────────────────────
def _encerrar_sem_janelas() -> None:
    """Encerra o servidor quando a última janela fecha e nenhuma tarefa está rodando."""
    ultimo_tique = time.monotonic()
    while True:
        time.sleep(2)
        agora = time.monotonic()
        # Depois de suspender o PC, o relógio salta: dá tempo de a janela voltar a dar sinal.
        if agora - ultimo_tique > 30:
            _ultimo_sinal["t"] = agora
        ultimo_tique = agora
        sinal = _ultimo_sinal["t"]
        if sinal and agora - sinal > TOLERANCIA_SEM_JANELA and not jobs.tem_trabalho_ativo():
            log.info("Nenhuma janela aberta. Encerrando.")
            jobs.limpar_tudo_na_inicializacao()
            _remover_pid()
            os._exit(0)


def _arquivo_pid() -> str:
    return str(config.INSTANCE_DIR / "prisma.pid")


def _remover_pid() -> None:
    try:
        os.remove(_arquivo_pid())
    except OSError:
        pass


def _prisma_na_porta(porta: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{porta}/health", timeout=2) as r:
            return json.load(r).get("service") == "prisma-converter"
    except (OSError, ValueError):
        return False


def _porta_livre(porta: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", porta)) != 0


def _abrir_janela(url: str) -> None:
    """Abre em modo aplicativo (sem barra de endereços), com o navegador padrão como reserva."""
    raizes = [os.environ.get(v) for v in ("ProgramFiles(x86)", "ProgramFiles", "LocalAppData")]
    candidatos = [shutil.which("msedge"), shutil.which("chrome")]
    for raiz in filter(None, raizes):
        candidatos += [os.path.join(raiz, r"Microsoft\Edge\Application\msedge.exe"),
                       os.path.join(raiz, r"Google\Chrome\Application\chrome.exe")]
    for executavel in filter(None, candidatos):
        if os.path.isfile(executavel):
            try:
                subprocess.Popen([executavel, f"--app={url}"])
                return
            except OSError as e:
                log.debug("Falha ao abrir %s: %s", executavel, e)
    webbrowser.open(url)


def main() -> int:
    from waitress import serve

    porta = int(os.environ.get("PORT", PORTA_PADRAO))
    if _prisma_na_porta(porta):
        log.info("Prisma já em execução na porta %s.", porta)
        if os.environ.get("NO_BROWSER") != "1":
            _abrir_janela(f"http://127.0.0.1:{porta}")
        return 0
    if not _porta_livre(porta):
        # Outro programa ocupa a porta: pede uma livre em vez de abrir o programa errado.
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            porta = s.getsockname()[1]
        log.warning("Porta padrão ocupada por outro programa. Usando %s.", porta)

    jobs.limpar_tudo_na_inicializacao()
    jobs.iniciar_limpeza()
    preparar_ffmpeg()
    with open(_arquivo_pid(), "w", encoding="ascii") as f:
        f.write(str(os.getpid()))

    if os.environ.get("NO_BROWSER") != "1":
        threading.Timer(1.0, _abrir_janela, args=(f"http://127.0.0.1:{porta}",)).start()
    if os.environ.get("NO_AUTO_SHUTDOWN") != "1":
        threading.Thread(target=_encerrar_sem_janelas, daemon=True, name="encerramento").start()

    log.info("Prisma em http://127.0.0.1:%s", porta)
    try:
        serve(app, host="127.0.0.1", port=porta, threads=12, ident="Prisma",
              max_request_body_size=config.MAX_UPLOAD_BYTES, channel_timeout=3600)
    finally:
        _remover_pid()
    return 0


if __name__ == "__main__":
    sys.exit(main())
