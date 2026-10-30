"""security.py — Proteções do servidor local: origem, CSRF, cabeçalhos e validação de entrada."""
import hmac
import ipaddress
import os
import re
import secrets
import socket
import zipfile
from urllib.parse import urlparse

from flask import abort, jsonify, redirect, request, session

from core.config import HOSTS_PERMITIDOS
from core.errors import ErroUsuario

EXT_AUDIO = {"mp3", "wav", "ogg", "flac", "aac", "m4a", "wma", "aiff", "aif", "ape", "opus", "webm", "mp4", "m4b", "3gp"}
EXT_VIDEO = {"mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "m4v", "3gp"}
EXT_IMAGEM = {"png", "jpg", "jpeg", "webp", "heic", "bmp", "gif", "tiff"}
EXT_PLANILHA = {"csv", "xlsx", "json"}

ZIP_MAX_DESCOMPRIMIDO = 4 * 1024 * 1024 * 1024
ZIP_MAX_RAZAO = 1000
FORMATOS_ZIP = {"docx", "xlsx", "pptx"}

_CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "media-src 'self' blob:",
    "font-src 'self'",
    "object-src 'self'",
    "frame-src 'self'",
    "connect-src 'self'",
    "base-uri 'none'",
    "form-action 'self'",
    "frame-ancestors 'self'",
])

_ROTAS_SEM_CSRF = {"/api/heartbeat"}


# ── Origem das requisições ────────────────────────────────────
def _host_valido(host: str) -> bool:
    return (host or "").rsplit(":", 1)[0].lower() in HOSTS_PERMITIDOS


def proteger_requisicao():
    """before_request: bloqueia DNS rebinding, chamadas de outros sites e CSRF."""
    if not _host_valido(request.host):
        abort(403)
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return None

    origem = request.headers.get("Origin")
    if origem and urlparse(origem).netloc != request.host:
        return jsonify({"erro": "Origem não permitida."}), 403
    if request.headers.get("Sec-Fetch-Site") in ("cross-site", "same-site"):
        return jsonify({"erro": "Origem não permitida."}), 403
    if request.path not in _ROTAS_SEM_CSRF and not validar_csrf():
        if not request.path.startswith("/api/"):
            return redirect("/conversor")
        return jsonify({"erro": "Sua sessão expirou. Recarregue a página."}), 403
    return None


def gerar_csrf() -> str:
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def validar_csrf() -> bool:
    esperado = session.get("csrf_token")
    if not esperado:
        return False
    enviado = request.headers.get("X-CSRFToken") or request.form.get("csrf_token") or ""
    return hmac.compare_digest(str(enviado), str(esperado))


def aplicar_cabecalhos(resposta):
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["X-Frame-Options"] = "SAMEORIGIN"
    # "no-referrer" faria o navegador enviar Origin: null nos formulários, recusados acima.
    resposta.headers["Referrer-Policy"] = "same-origin"
    resposta.headers["Content-Security-Policy"] = _CSP
    resposta.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    return resposta


# ── Nomes e arquivos ──────────────────────────────────────────
_RESERVADOS = {"con", "prn", "aux", "nul", *{f"com{i}" for i in range(1, 10)}, *{f"lpt{i}" for i in range(1, 10)}}


def nome_seguro(nome: str, padrao: str = "arquivo") -> str:
    """Remove caminhos e caracteres inválidos, preservando acentos e outros alfabetos."""
    nome = (nome or "").replace("\\", "/").rsplit("/", 1)[-1]
    nome = re.sub(r'[<>:"|?*\x00-\x1f]', "_", nome).strip(" .")
    base, ext = os.path.splitext(nome)
    base = base[:140]
    if not base.strip("_ .") or base.split(".", 1)[0].lower() in _RESERVADOS:
        base = padrao
    return base + ext[:12]


def obter_extensao(nome: str) -> str:
    return nome.rsplit(".", 1)[-1].lower() if "." in nome else ""


_ASSINATURAS = {
    "pdf": [b"%PDF"],
    "docx": [b"PK\x03\x04"], "xlsx": [b"PK\x03\x04"], "pptx": [b"PK\x03\x04"],
    "doc": [b"\xd0\xcf\x11\xe0"], "xls": [b"\xd0\xcf\x11\xe0"], "ppt": [b"\xd0\xcf\x11\xe0"],
    "png": [b"\x89PNG"], "gif": [b"GIF87a", b"GIF89a"], "jpg": [b"\xff\xd8\xff"], "jpeg": [b"\xff\xd8\xff"],
}


def validar_magic(caminho: str, ext: str) -> bool:
    """Confere se o conteúdo corresponde à extensão, nos formatos com assinatura conhecida."""
    ext = (ext or "").lower()
    try:
        with open(caminho, "rb") as f:
            cabecalho = f.read(4096)
    except OSError:
        return False
    if not cabecalho:
        return False
    if ext == "webp":
        return cabecalho[:4] == b"RIFF" and cabecalho[8:12] == b"WEBP"
    if ext == "heic":
        return cabecalho[4:8] == b"ftyp"
    if ext == "json":
        texto = cabecalho.decode("utf-8", errors="ignore").lstrip("﻿ \t\r\n")
        return bool(texto) and texto[0] in "{["
    assinaturas = _ASSINATURAS.get(ext)
    return True if assinaturas is None else any(cabecalho.startswith(a) for a in assinaturas)


def verificar_zip_bomb(caminho: str) -> bool:
    """Retorna False se o ZIP (ou DOCX/XLSX/PPTX) é inválido ou se expande de forma suspeita."""
    try:
        with zipfile.ZipFile(caminho) as zf:
            total = sum(i.file_size for i in zf.infolist())
        tamanho = os.path.getsize(caminho)
        return total <= ZIP_MAX_DESCOMPRIMIDO and (not tamanho or total / tamanho <= ZIP_MAX_RAZAO)
    except (zipfile.BadZipFile, OSError):
        return False


def validar_entrada(caminho: str, ext: str) -> None:
    if not validar_magic(caminho, ext):
        raise ErroUsuario(f"O conteúdo do arquivo não corresponde ao formato .{ext}.")
    if ext in FORMATOS_ZIP and not verificar_zip_bomb(caminho):
        raise ErroUsuario("Arquivo recusado: conteúdo compactado inválido ou grande demais.")


# ── URLs externas ─────────────────────────────────────────────
def validar_url_externa(url: str) -> str:
    """Aceita só http(s) para endereços públicos, impedindo acesso à rede interna."""
    url = (url or "").strip()
    partes = urlparse(url)
    if partes.scheme not in ("http", "https") or not partes.hostname:
        raise ErroUsuario("Informe uma URL válida (ex.: https://youtube.com/watch?v=...).")
    try:
        enderecos = {info[4][0] for info in socket.getaddrinfo(partes.hostname, partes.port or 443)}
    except (socket.gaierror, UnicodeError):
        raise ErroUsuario("Não foi possível encontrar esse endereço. Verifique a URL e sua conexão.") from None
    for endereco in enderecos:
        if not ipaddress.ip_address(endereco.split("%", 1)[0]).is_global:
            raise ErroUsuario("Endereços da rede local não são permitidos.")
    return url
