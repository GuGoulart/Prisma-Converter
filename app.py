from flask import (Flask, render_template, request, send_file,
                   session, after_this_request, abort, Response)
from converter import obter_conversoes, converter_arquivo, obter_motor, detectar_encoding
from pdf_tools import mesclar_pdfs, dividir_pdf, proteger_pdf, desproteger_pdf
from werkzeug.utils import secure_filename
from datetime import datetime
from collections import defaultdict
from threading import Lock
from dotenv import load_dotenv

import os, re, secrets, shutil, time, uuid, logging, threading, traceback
import pandas as pd

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-local-key")

UPLOAD_FOLDER   = "uploads"
DOWNLOAD_FOLDER = "downloads"
MAX_MB          = 50
TIMEOUT_CONV    = 120
TIMEOUT_PREVIEW = 40

app.config["UPLOAD_FOLDER"]      = UPLOAD_FOLDER
app.config["DOWNLOAD_FOLDER"]    = DOWNLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024

os.makedirs(UPLOAD_FOLDER,   exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

contador_conversoes = 0

logging.basicConfig(
    filename="prisma.log", level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)


# ── Segurança ─────────────────────────────────────────────────

@app.after_request
def cabecalhos_seguranca(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]         = "SAMEORIGIN"
    response.headers["X-XSS-Protection"]        = "1; mode=block"
    response.headers["Referrer-Policy"]          = "no-referrer"
    return response


_contagem_ip = defaultdict(list)
_lock_rate   = Lock()

def verificar_rate_limit(ip):
    agora = time.time()
    with _lock_rate:
        _contagem_ip[ip] = [t for t in _contagem_ip[ip] if agora - t < 60]
        if len(_contagem_ip[ip]) >= 10: return False
        _contagem_ip[ip].append(agora)
        return True


_conversoes_ativas = 0
_lock_conv         = Lock()
MAX_PARALELAS      = 3


def gerar_csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]

def validar_csrf(tok):
    return bool(tok and tok == session.get("csrf_token"))


LIMITES_POR_TIPO = {
    "csv":5*1024*1024,  "xlsx":20*1024*1024, "xls":20*1024*1024,
    "pdf":50*1024*1024, "docx":20*1024*1024, "doc":20*1024*1024,
    "ppt":50*1024*1024, "pptx":50*1024*1024,
    "png":10*1024*1024, "jpg":10*1024*1024,  "jpeg":10*1024*1024,
}
NOMES_LIMITES = {k: f"{v//(1024*1024)} MB" for k, v in LIMITES_POR_TIPO.items()}

_EXT_PERIGOSAS = {
    "exe","bat","cmd","com","php","sh","ps1","vbs","js",
    "jar","py","rb","pl","asp","jsp","cgi","msi","dll"
}

_MAGIC = {
    "pdf":  [b"%PDF"],
    "docx": [b"PK\x03\x04"], "xlsx": [b"PK\x03\x04"], "pptx": [b"PK\x03\x04"],
    "ppt":  [b"\xd0\xcf\x11\xe0"], "doc": [b"\xd0\xcf\x11\xe0"], "xls": [b"\xd0\xcf\x11\xe0"],
    "png":  [b"\x89PNG"],
    "jpg":  [b"\xff\xd8\xff"], "jpeg": [b"\xff\xd8\xff"],
    "csv":  None,
}

def validar_nome(nome):
    p = nome.split(".")
    return len(p) <= 2 or not any(x.lower() in _EXT_PERIGOSAS for x in p[1:-1])

def validar_magic(caminho, ext):
    m = _MAGIC.get(ext)
    if m is None: return True
    try:
        with open(caminho, "rb") as f: h = f.read(8)
        return any(h.startswith(x) for x in m)
    except: return False


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
        elif extensao in ("xlsx", "xls"):
            df = pd.read_excel(caminho, nrows=limite, engine="openpyxl")
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

def _limpar_residuos():
    limite = 15 * 60
    while True:
        time.sleep(900)
        agora = time.time()
        for pasta in [UPLOAD_FOLDER, DOWNLOAD_FOLDER]:
            for item in os.listdir(pasta):
                c = os.path.join(pasta, item)
                try:
                    if agora - os.path.getmtime(c) > limite:
                        if os.path.isdir(c): shutil.rmtree(c, ignore_errors=True)
                        else: os.remove(c)
                except: pass

threading.Thread(target=_limpar_residuos, daemon=True).start()


# ── Context processor ─────────────────────────────────────────

@app.context_processor
def inject_globals():
    return dict(
        contador=contador_conversoes,
        historico=session.get("historico", []),
        motor=obter_motor(),
        csrf_token=gerar_csrf(),
    )

@app.errorhandler(413)
def arquivo_grande(e):
    return render_template("index.html",
                           erro=f"Arquivo muito grande. Limite: {MAX_MB} MB."), 413


# ── Rotas ─────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ferramentas-pdf")
def pdf_tools_page():
    return render_template("pdf_tools.html")

@app.route("/api/pdf/mesclar", methods=["POST"])
def api_mesclar():
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
        
    saida = os.path.join(pp, "mesclado.pdf")
    try:
        mesclar_pdfs(caminhos, saida)
        @after_this_request
        def cleanup(response):
            threading.Thread(target=lambda: (time.sleep(2), shutil.rmtree(pp, ignore_errors=True))).start()
            return response
        return send_file(saida, as_attachment=True, download_name="Prisma_Mesclado.pdf")
    except Exception as e:
        return render_template("pdf_tools.html", erro=str(e)), 400

@app.route("/api/pdf/dividir", methods=["POST"])
def api_dividir():
    f = request.files.get("arquivo")
    if not f: return "Selecione um arquivo", 400
    
    modo = request.form.get("modo", "individual")
    parametro = request.form.get("parametro", "")
    
    uid = criar_pasta()
    pp = pasta_path(uid)
    entrada = os.path.join(pp, secure_filename(f.filename))
    f.save(entrada)
    
    saida = os.path.join(pp, "dividido.zip")
    try:
        dividir_pdf(entrada, saida, modo, parametro)
        @after_this_request
        def cleanup(response):
            threading.Thread(target=lambda: (time.sleep(2), shutil.rmtree(pp, ignore_errors=True))).start()
            return response
        return send_file(saida, as_attachment=True, download_name="Prisma_Dividido.zip")
    except Exception as e:
        return render_template("pdf_tools.html", erro=str(e)), 400

@app.route("/api/pdf/proteger", methods=["POST"])
def api_proteger():
    f = request.files.get("arquivo")
    senha = request.form.get("senha")
    if not f or not senha: return "Arquivo e senha são obrigatórios", 400
    
    uid = criar_pasta()
    pp = pasta_path(uid)
    entrada = os.path.join(pp, secure_filename(f.filename))
    f.save(entrada)
    
    saida = os.path.join(pp, "protegido.pdf")
    try:
        proteger_pdf(entrada, senha, saida)
        @after_this_request
        def cleanup(response):
            threading.Thread(target=lambda: (time.sleep(2), shutil.rmtree(pp, ignore_errors=True))).start()
            return response
        return send_file(saida, as_attachment=True, download_name="Prisma_Protegido.pdf")
    except Exception as e:
        return render_template("pdf_tools.html", erro=str(e)), 400

@app.route("/api/pdf/desproteger", methods=["POST"])
def api_desproteger():
    f = request.files.get("arquivo")
    senha = request.form.get("senha")
    if not f or not senha: return "Arquivo e senha são obrigatórios", 400
    
    uid = criar_pasta()
    pp = pasta_path(uid)
    entrada = os.path.join(pp, secure_filename(f.filename))
    f.save(entrada)
    
    saida = os.path.join(pp, "desprotegido.pdf")
    try:
        desproteger_pdf(entrada, senha, saida)
        @after_this_request
        def cleanup(response):
            threading.Thread(target=lambda: (time.sleep(2), shutil.rmtree(pp, ignore_errors=True))).start()
            return response
        return send_file(saida, as_attachment=True, download_name="Prisma_Desprotegido.pdf")
    except Exception as e:
        return render_template("pdf_tools.html", erro=str(e)), 400


@app.route("/preview/<pasta_uuid>/<preview_file>")
def preview_arquivo(pasta_uuid, preview_file):
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
    if session.get("pasta_upload") != pasta_uuid:
        abort(403)
    if destino not in {"pdf","png","jpg","csv","xlsx","docx","pptx","ppt"}:
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
            abort(500, description=str(err[0]) if err[0] else "Erro ao gerar prévia")

    return send_file(prev_path)


@app.route("/preview-tabela/<pasta_uuid>/<destino>")
def preview_tabela(pasta_uuid, destino):
    if session.get("pasta_upload") != pasta_uuid:
        abort(403)
    if destino not in ("csv", "xlsx"):
        abort(400)

    extensao     = session.get("arquivo_ext", "")
    arquivo_nome = session.get("arquivo_nome", "")
    pp           = pasta_path(pasta_uuid)
    entrada      = os.path.join(pp, arquivo_nome)

    if not os.path.exists(entrada):
        abort(404)

    # Sempre mostra os dados reais do arquivo original
    # Se o arquivo já é CSV/XLSX, lê direto; senão converte
    if extensao in ("csv", "xlsx", "xls"):
        alvo     = entrada
        alvo_ext = extensao
    else:
        # Converte para o destino pedido e mostra
        cache = os.path.join(pp, f"prev_{destino}.{destino}")
        if not os.path.exists(cache):
            try:
                converter_arquivo(entrada, cache, extensao, destino)
            except Exception as e:
                return Response(
                    f"<p class='prev-erro-msg'>Erro ao converter: {e}</p>",
                    status=500
                )
        alvo     = cache
        alvo_ext = destino

    # Sem limite de linhas — mostra tudo
    tabela = gerar_preview_tabela(alvo, alvo_ext, limite=None)

    if tabela:
        return Response(tabela, content_type="text/html")
    return Response(
        "<p class='prev-erro-msg'>Não foi possível gerar a tabela.</p>",
        status=500
    )


@app.route("/upload", methods=["POST"])
def upload():
    global contador_conversoes
    ip = request.remote_addr

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

        ext      = nome_original.rsplit(".", 1)[1].lower()
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

        elif ext in ("png", "jpg", "jpeg"):
            preview_url  = f"/preview/{uid}/{nome_i}"
            preview_tipo = "imagem"

        elif ext in ("csv", "xlsx", "xls"):
            tabela_html = gerar_preview_tabela(cam, ext, limite=None)

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
        return render_template("index.html", erro=str(e))


@app.route("/converter", methods=["POST"])
def converter():
    global _conversoes_ativas, contador_conversoes
    ip = request.remote_addr

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
            except: pass
            try:
                if saida and os.path.exists(saida): os.remove(saida)
            except: pass
            return resp

        contador_conversoes += 1
        log.info(f"OK: {nome_original} | {origem.upper()}→{destino.upper()} | {ip}")

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
        if download_token:
            resp.set_cookie("downloadToken", download_token,
                            max_age=60, samesite="Lax")
        return resp

    except Exception as e:
        log.error(f"Conversão error — {traceback.format_exc()}")
        try: shutil.rmtree(pp, ignore_errors=True)
        except: pass
        return render_template("index.html", erro=str(e))
    finally:
        with _lock_conv:
            _conversoes_ativas -= 1


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)