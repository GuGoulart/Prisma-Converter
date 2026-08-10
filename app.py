import os
import sys
import time
import secrets
import logging
import threading
from flask import Flask, render_template, session, jsonify
from dotenv import load_dotenv

from core.security import gerar_csrf
from core.cleanup import iniciar_limpeza
from core.converter import obter_motor, CONVERSOES
from core.storage import storage
from routes import registrar_blueprints

class HeartbeatLogFilter(logging.Filter):
    def filter(self, record):
        return "/api/heartbeat" not in record.getMessage()

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
logging.getLogger("werkzeug").addFilter(HeartbeatLogFilter())
log = logging.getLogger(__name__)

load_dotenv()


# ── Configuração de empacotamento PyInstaller / Flask ─────────────────────────
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

UPLOAD_FOLDER = "uploads"
DOWNLOAD_FOLDER = "downloads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

_IS_RENDER = os.environ.get("RENDER") in ("true", "1") or bool(os.environ.get("RENDER_SERVICE_ID"))
_IS_DESKTOP = (os.environ.get("PRISMA_DESKTOP") == "1") or (not _IS_RENDER)
_IS_WEB = not _IS_DESKTOP

MAX_MB = int(os.environ.get("MAX_MB", "10").strip()) if _IS_WEB else 0
MAX_OUTPUT_MB = int(os.environ.get("MAX_OUTPUT_MB", "50").strip()) if _IS_WEB else 0


# ── Inicializar módulos ────────────────────────────────────────────────────────
iniciar_limpeza(UPLOAD_FOLDER, DOWNLOAD_FOLDER)
registrar_blueprints(app)


def _formatar_tamanho(b):
    if not isinstance(b, (int, float)):
        return "Indisponível"
    if b < 1024:
        return f"{b} B"
    if b < 1048576:
        return f"{b / 1024:.1f} KB"
    return f"{b / 1048576:.1f} MB"


# ── Context Processor (Injeta variáveis globais nos HTMLs) ────────────────────
@app.context_processor
def inject_globals():
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

        if destruido or (policy == "instant" and baixado) or (expira_em and agora > expira_em) or (caminho and not storage.existe(caminho)):
            item["apagado"] = True
        else:
            item["apagado"] = False

    from routes.converter import contador_conversoes
    return dict(
        contador=contador_conversoes,
        historico=hist,
        retencao_padrao=current_policy,
        motor=obter_motor(),
        csrf_token=gerar_csrf(),
        todas_conversoes=CONVERSOES,
        max_mb=MAX_MB,
        max_output_mb=MAX_OUTPUT_MB,
    )



# ── Error Handlers ────────────────────────────────────────────────────────────
@app.after_request
def aplicar_headers_seguranca(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


@app.errorhandler(413)

def arquivo_grande(e):
    return render_template("index.html", erro=f"Arquivo muito grande. Limite: {MAX_MB} MB."), 413

@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def erro_interno_servidor(e):
    return render_template("500.html"), 500


# ── Monitor de Auto-Shutdown Desktop ──────────────────────────────────────────
_ultimo_heartbeat = time.time()
_inicio_servidor = time.time()

@app.route('/api/heartbeat', methods=['POST', 'GET'])
def api_heartbeat():
    global _ultimo_heartbeat
    _ultimo_heartbeat = time.time()
    return jsonify({"status": "ok"})


def _monitorar_encerramento_auto():
    global _ultimo_heartbeat, _inicio_servidor
    time.sleep(10)
    while True:
        time.sleep(2)
        agora = time.time()
        if (agora - _ultimo_heartbeat > 6) and (agora - _inicio_servidor > 12):
            log.info("[desktop] Nenhuma aba ativa do navegador detectada por mais de 6s. Encerrando servidor Python automaticamente...")
            time.sleep(0.3)
            os._exit(0)


def _abrir_navegador_auto(port):
    import webbrowser
    time.sleep(1.2)
    url = f"http://127.0.0.1:{port}"
    try:
        webbrowser.open(url)
    except Exception as e:
        log.warning(f"[desktop] Não foi possível abrir o navegador automaticamente: {e}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG") == "1"

    if _IS_DESKTOP and os.environ.get("NO_BROWSER") != "1":
        is_reloader = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
        if (not debug_mode) or is_reloader:
            threading.Thread(target=_abrir_navegador_auto, args=(port,), daemon=True).start()
            threading.Thread(target=_monitorar_encerramento_auto, daemon=True).start()

    app.run(debug=debug_mode, host="0.0.0.0", port=port)