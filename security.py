import os
import secrets
from flask import session
import time
from collections import defaultdict
from threading import Lock

_contagem_ip = defaultdict(list)
_lock_rate   = Lock()

def verificar_rate_limit(ip):
    agora = time.time()
    with _lock_rate:
        _contagem_ip[ip] = [t for t in _contagem_ip[ip] if agora - t < 60]
        if len(_contagem_ip[ip]) >= 10: return False
        _contagem_ip[ip].append(agora)
        return True

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
