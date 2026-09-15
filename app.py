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

try:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
except Exception:
    pass

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# ── Chave secreta ─────────────────────────────────────────────────────────────
_sec_key = (os.environ.get("SECRET_KEY") or "").strip()
if not _sec_key:
    _IS_RENDER = os.environ.get("RENDER") in ("true", "1") or bool(os.environ.get("RENDER_SERVICE_ID"))
    if _IS_RENDER:
        log.warning("[seguranca] SECRET_KEY nao configurada. Gerando chave temporaria.")
        _sec_key = secrets.token_hex(32)
    else:
        _sec_key = "prisma_converter_default_secret_key_dev_2026"
app.secret_key = _sec_key

# ── Diretórios de trabalho ────────────────────────────────────────────────────
UPLOAD_FOLDER = "uploads"
DOWNLOAD_FOLDER = "downloads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

_IS_RENDER = os.environ.get("RENDER") in ("true", "1") or bool(os.environ.get("RENDER_SERVICE_ID"))
_IS_DESKTOP = not _IS_RENDER
MAX_MB = int(os.environ.get("MAX_MB", "50").strip()) if not _IS_DESKTOP else 0


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


# ── Ponto de entrada ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG") == "1"

    if _IS_DESKTOP and os.environ.get("NO_BROWSER") != "1":
        def _abrir_navegador():
            import webbrowser
            time.sleep(1.2)
            webbrowser.open(f"http://127.0.0.1:{port}")

        is_reloader = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
        if (not debug_mode) or is_reloader:
            threading.Thread(target=_abrir_navegador, daemon=True).start()

    app.run(debug=debug_mode, host="0.0.0.0", port=port)
