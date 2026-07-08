from flask import (Flask, render_template, request, send_file,
                   session, after_this_request, abort, Response)
from core.converter import obter_conversoes, converter_arquivo, obter_motor, detectar_encoding, remover_fundo_imagem, mesclar_planilhas
from core.pdf_tools import mesclar_pdfs, dividir_pdf, proteger_pdf, desproteger_pdf, comprimir_pdf, adicionar_marca_dagua, extrair_imagens_pdf, manipular_paginas_pdf
from werkzeug.utils import secure_filename
from datetime import datetime
from collections import defaultdict
from threading import Lock
from core.security import gerar_csrf, validar_csrf, verificar_rate_limit, validar_nome, validar_magic, rate_limit_required
from core.cleanup import iniciar_limpeza
import sys
from dotenv import load_dotenv

import os, re, secrets, shutil, time, uuid, logging, threading, traceback

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

UPLOAD_FOLDER   = "uploads"
DOWNLOAD_FOLDER = "downloads"
MAX_MB          = 15
TIMEOUT_CONV    = 120
TIMEOUT_PREVIEW = 40

app.config["UPLOAD_FOLDER"]      = UPLOAD_FOLDER
app.config["DOWNLOAD_FOLDER"]    = DOWNLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024

os.makedirs(UPLOAD_FOLDER,   exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

contador_conversoes = 0

logging.basicConfig(
    stream=sys.stdout, level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

_conversoes_ativas = 0
_lock_conv         = Lock()
MAX_PARALELAS      = 1

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
}
NOMES_LIMITES = {k: f"{MAX_MB} MB" for k in LIMITES_POR_TIPO}


# ── Segurança ─────────────────────────────────────────────────

@app.after_request
def cabecalhos_seguranca(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]         = "SAMEORIGIN"
    response.headers["X-XSS-Protection"]        = "1; mode=block"
    response.headers["Referrer-Policy"]          = "no-referrer"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"]   = "default-src 'self'; script-src 'self' 'unsafe-inline'; font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com"
    return response




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
        elif extensao in ("xlsx", "xls"):
            df = pd.read_excel(caminho, nrows=limite, engine="openpyxl")
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

@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def erro_interno_servidor(e):
    return render_template("500.html"), 500

@app.route('/health')
def health_check():
    return {"status": "ok"}, 200

@app.route('/favicon.ico')
def favicon():
    return "", 204

# ── Rotas ─────────────────────────────────────────────────────

@app.context_processor
def inject_globals():
    from core.converter import CONVERSOES
    return dict(todas_conversoes=CONVERSOES)

@app.route("/")
def home():
    return render_template("index.html")

from flask import redirect, url_for

@app.route("/ferramentas-pdf")
def redirect_ferramentas():
    return redirect(url_for("ferramentas_pdf_page"))

@app.route("/ferramentas-avancadas")
def ferramentas_pdf_page():
    return render_template("pdf_tools.html")

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
    
    saida = os.path.join(pp, "comprimido.pdf")
    try:
        comprimir_pdf(entrada, saida, nivel=nivel)
        @after_this_request
        def cleanup(response):
            threading.Thread(target=lambda: (time.sleep(2), shutil.rmtree(pp, ignore_errors=True))).start()
            return response
        return send_file(saida, as_attachment=True, download_name="Prisma_Comprimido.pdf")
    except Exception as e:
        return render_template("pdf_tools.html", erro=str(e)), 400

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
    
    saida = os.path.join(pp, "marcado.pdf")
    try:
        adicionar_marca_dagua(entrada, texto, saida)
        @after_this_request
        def cleanup(response):
            threading.Thread(target=lambda: (time.sleep(2), shutil.rmtree(pp, ignore_errors=True))).start()
            return response
        return send_file(saida, as_attachment=True, download_name="Prisma_Marcado.pdf")
    except Exception as e:
        return render_template("pdf_tools.html", erro=str(e)), 400

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
    
    saida = os.path.join(pp, "imagens.zip")
    try:
        extrair_imagens_pdf(entrada, saida)
        @after_this_request
        def cleanup(response):
            threading.Thread(target=lambda: (time.sleep(2), shutil.rmtree(pp, ignore_errors=True))).start()
            return response
        return send_file(saida, as_attachment=True, download_name="Prisma_Imagens_PDF.zip")
    except Exception as e:
        return render_template("pdf_tools.html", erro=str(e)), 400

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
    
    saida = os.path.join(pp, "manipulado.pdf")
    try:
        manipular_paginas_pdf(entrada, saida, remover, rotacionar)
        @after_this_request
        def cleanup(response):
            threading.Thread(target=lambda: (time.sleep(2), shutil.rmtree(pp, ignore_errors=True))).start()
            return response
        return send_file(saida, as_attachment=True, download_name="Prisma_Paginas_Manipuladas.pdf")
    except Exception as e:
        return render_template("pdf_tools.html", erro=str(e)), 400

@app.route("/api/img/remover-fundo", methods=["POST"])
@rate_limit_required
def api_remover_fundo():
    if not validar_csrf(request.form.get('csrf_token', '')):
        return render_template("pdf_tools.html", erro="Token inválido. Recarregue a página."), 403

    f = request.files.get("arquivo")
    if not f: return "Selecione um arquivo", 400
    
    uid = criar_pasta()
    pp = pasta_path(uid)
    entrada = os.path.join(pp, secure_filename(f.filename))
    f.save(entrada)
    
    saida = os.path.join(pp, "sem_fundo.png")
    try:
        remover_fundo_imagem(entrada, saida)
        @after_this_request
        def cleanup(response):
            threading.Thread(target=lambda: (time.sleep(2), shutil.rmtree(pp, ignore_errors=True))).start()
            return response
        return send_file(saida, as_attachment=True, download_name="Prisma_Sem_Fundo.png")
    except Exception as e:
        return render_template("index.html", erro=str(e)), 400

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
        
    saida = os.path.join(pp, f"mesclado.{formato}")
    try:
        mesclar_planilhas(caminhos, saida, formato)
        @after_this_request
        def cleanup(response):
            threading.Thread(target=lambda: (time.sleep(2), shutil.rmtree(pp, ignore_errors=True))).start()
            return response
        return send_file(saida, as_attachment=True, download_name=f"Prisma_Mesclado.{formato}")
    except Exception as e:
        return render_template("index.html", erro=str(e)), 400

@app.route("/manifest.json")
def serve_manifest():
    return send_file("static/manifest.json", mimetype="application/manifest+json")

@app.route("/sw.js")
def serve_sw():
    return send_file("static/sw.js", mimetype="application/javascript")


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
    if destino not in {"pdf","png","jpg","csv","xlsx","docx","pptx","ppt","json","webp","heic","txt"}:
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
                return Response(
                    f"<p class='prev-erro-msg'>Erro ao converter: {e}</p>",
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

        elif ext in ("png", "jpg", "jpeg", "webp", "heic"):
            preview_url  = f"/preview/{uid}/{nome_i}"
            preview_tipo = "imagem"

        elif ext in ("csv", "xlsx", "xls", "json"):
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
    debug_mode = os.environ.get("FLASK_DEBUG") == "1"
    app.run(debug=debug_mode, host="0.0.0.0", port=port)