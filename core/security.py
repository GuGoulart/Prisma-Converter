import os
import secrets
from flask import session
import time
from collections import defaultdict
from threading import Lock

_contagem_ip = defaultdict(list)
_lock_rate   = Lock()

def extrair_ip_cliente(req):
    """Extrai o IP real do cliente, respeitando proxies reversos (X-Forwarded-For)."""
    if req is None:
        return "127.0.0.1"
    xf = req.headers.get("X-Forwarded-For")
    if xf:
        return xf.split(",")[0].strip()
    return req.remote_addr or "127.0.0.1"

def verificar_rate_limit(ip):
    agora = time.time()
    with _lock_rate:
        _contagem_ip[ip] = [t for t in _contagem_ip[ip] if agora - t < 60]
        if len(_contagem_ip[ip]) >= 10: return False
        _contagem_ip[ip].append(agora)
        return True

def rate_limit_required(f):
    from functools import wraps
    from flask import request
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = extrair_ip_cliente(request)
        if not verificar_rate_limit(ip):
            return "Muitas requisições. Aguarde um momento.", 429
        return f(*args, **kwargs)
    return decorated_function

def gerar_csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]

def validar_csrf(tok):
    return bool(tok and tok == session.get("csrf_token"))

_EXT_PERIGOSAS = {
    "exe","bat","cmd","com","php","sh","ps1","vbs","js",
    "jar","py","rb","pl","asp","jsp","cgi","msi","dll"
}

_MAGIC = {
    "pdf":  [b"%PDF"],
    "docx": [b"PK\x03\x04"], "xlsx": [b"PK\x03\x04"], "pptx": [b"PK\x03\x04"],
    "ppt":  [b"\xd0\xcf\x11\xe0"], "doc": [b"\xd0\xcf\x11\xe0"], "xls": [b"\xd0\xcf\x11\xe0"],
    "png":  [b"\x89PNG"],
    "gif":  [b"GIF87a", b"GIF89a"],
    "jpg":  [b"\xff\xd8\xff"], "jpeg": [b"\xff\xd8\xff"],
    "mp4":  "special",
    "mp3":  [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID3"],
    "enc":  None,  # arquivo criptografado, sem magic definido
    # Formatos com validação especial (ver validar_magic abaixo)
    "webp": "special",
    "heic": "special",
    "json": "special",
    "csv":  None,   # texto puro — sem magic bytes confiáveis
    "txt":  None,   # texto puro
}

def validar_nome(nome):
    p = nome.split(".")
    if len(p) < 2:
        return True
    return not any(x.lower() in _EXT_PERIGOSAS for x in p[1:])

def validar_magic(caminho, ext):
    m = _MAGIC.get(ext)

    # Sem validação definida (CSV, TXT, formatos desconhecidos)
    if m is None:
        return True

    # Validações especiais por formato
    if m == "special":
        try:
            with open(caminho, "rb") as f:
                header = f.read(16)
        except OSError:
            return False

        if ext == "webp":
            # WEBP: bytes 0-3 = "RIFF", bytes 8-11 = "WEBP"
            return len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP"

        if ext == "heic":
            # HEIC/HEIF: box 'ftyp' nos bytes 4-8
            return len(header) >= 8 and header[4:8] == b"ftyp"

        if ext == "json":
            # JSON deve começar com { ou [ (após possível BOM/espaço)
            try:
                with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                    first = f.read(4096).lstrip()
                return bool(first) and first[0] in ("{", "[")
            except OSError:
                return False

        if ext == "mp4":
            # MP4/M4A: box 'ftyp' nos bytes 4-8
            return len(header) >= 8 and header[4:8] == b"ftyp"

        return True  # fallback para "special" desconhecidos

    # Validação padrão por magic bytes (comparação de prefixo)
    try:
        with open(caminho, "rb") as f:
            h = f.read(8)
        return any(h.startswith(x) for x in m)
    except OSError:
        return False
