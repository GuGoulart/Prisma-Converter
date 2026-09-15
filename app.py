"""
app.py — Ponto de entrada principal do Prisma Converter.

Integra as ferramentas do Prisma Converter (documentos, PDF, imagens, QR Code)
com as do Prisma Audio (áudio, vídeo, download por link).
"""
import os
import sys
import secrets
import logging
import threading
import time

from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

from core.security import gerar_csrf
from core.cleanup import iniciar_limpeza
from core.converter import CONVERSOES
from routes import registrar_blueprints


# ── Logging ───────────────────────────────────────────────────────────────────

class HeartbeatLogFilter(logging.Filter):
    def filter(self, record):
        return "/api/heartbeat" not in record.getMessage()


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
)
logging.getLogger("werkzeug").addFilter(HeartbeatLogFilter())
log = logging.getLogger(__name__)

load_dotenv()

# ── Auto-configuração de FFmpeg (static-ffmpeg zero-config) ───────────────────
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
    log.info("[ffmpeg] Auto-configuracao estatica do FFmpeg ativada.")
except Exception as _e:
    log.debug(f"[ffmpeg] static_ffmpeg nao disponivel: {_e}")


# ── Criar app Flask ───────────────────────────────────────────────────────────

if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    app = Flask(__name__,
                template_folder=os.path.join(bundle_dir, 'templates'),
                static_folder=os.path.join(bundle_dir, 'static'))
else:
    app = Flask(__name__)

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# ── Chave secreta local ───────────────────────────────────────────────────────
_sec_key = (os.environ.get("SECRET_KEY") or "").strip()
if not _sec_key:
    _sec_key = "prisma_converter_local_app_secret_key"
app.secret_key = _sec_key

# ── Diretórios de trabalho ────────────────────────────────────────────────────
UPLOAD_FOLDER = "uploads"
DOWNLOAD_FOLDER = "downloads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ── Modo App Local (Sem limites de upload / estritamente local) ───────────────
MAX_MB = 0  # 0 = Sem limite em modo desktop local


# ── Verificar FFmpeg ──────────────────────────────────────────────────────────
def _verificar_ffmpeg():
    import subprocess
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            log.info("[ffmpeg] FFmpeg encontrado e funcional.")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    log.warning("[ffmpeg] FFmpeg nao encontrado no PATH. Ferramentas de audio/video podem nao funcionar.")
    return False


_ffmpeg_ok = _verificar_ffmpeg()


# ── Inicializar módulos ───────────────────────────────────────────────────────
iniciar_limpeza(UPLOAD_FOLDER, DOWNLOAD_FOLDER)
registrar_blueprints(app)


# ── Context Processor ─────────────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    return dict(
        csrf_token=gerar_csrf(),
        max_mb=MAX_MB,
        ffmpeg_ok=_ffmpeg_ok,
        todas_conversoes=CONVERSOES,
    )


# ── Security Headers ──────────────────────────────────────────────────────────
@app.after_request
def aplicar_headers_seguranca(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# ── Error Handlers ────────────────────────────────────────────────────────────
@app.errorhandler(413)
def arquivo_grande(e):
    return jsonify({"erro": f"Arquivo muito grande. Limite: {MAX_MB} MB."}), 413


@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def erro_interno_servidor(e):
    return render_template("500.html"), 500


# ── Heartbeat (keepalive para desktop) ───────────────────────────────────────
_ultimo_heartbeat = time.time()
_inicio_servidor = time.time()


@app.route('/api/heartbeat', methods=['POST', 'GET'])
def api_heartbeat():
    global _ultimo_heartbeat
    _ultimo_heartbeat = time.time()
    return jsonify({"status": "ok"})


def _porta_em_uso(porta, host="127.0.0.1"):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, porta)) == 0


def _abrir_janela_app(url):
    """Abre o Prisma em modo aplicativo de desktop (sem barra de URL do navegador)."""
    import subprocess
    import shutil
    import webbrowser

    time.sleep(1.0)

    # Navegadores compatíveis com --app (modo janela nativa desktop)
    candidatos = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        shutil.which("msedge"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        shutil.which("chrome"),
    ]

    for executavel in candidatos:
        if executavel and os.path.isfile(executavel):
            try:
                subprocess.Popen([executavel, f"--app={url}"])
                return
            except Exception as e:
                log.debug(f"Falha ao abrir via {executavel}: {e}")

    # Fallback para navegador padrao caso Edge/Chrome nao estejam disponiveis
    webbrowser.open(url)


# ── Ponto de entrada (Modo App Local) ─────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG") == "1"
    url = f"http://127.0.0.1:{port}"

    # Se a porta ja estiver aberta por outra instancia do Prisma, apenas foca a janela
    if _porta_em_uso(port):
        log.info(f"Prisma ja em execucao na porta {port}. Abrindo janela...")
        _abrir_janela_app(url)
        sys.exit(0)

    if os.environ.get("NO_BROWSER") != "1":
        is_reloader = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
        if (not debug_mode) or is_reloader:
            threading.Thread(target=_abrir_janela_app, args=(url,), daemon=True).start()

    app.run(debug=debug_mode, host="127.0.0.1", port=port)

