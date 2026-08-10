import os
import secrets
import zipfile
from flask import session
import time
from collections import defaultdict
from threading import Lock

_contagem_ip = defaultdict(list)
_lock_rate   = Lock()

# ─── Limites de segurança ────────────────────────────────────────────────────

# Tamanho máximo descomprimido de um ZIP (100 MB).
# Protege contra Zip Bomb: um arquivo .zip de 1 KB pode se expandir para GBs.
# ARQUITETURA: Se no futuro o serviço usar Redis, migrar esta lógica para um
# middleware distribuído (ex: Flask-Limiter com Redis storage).
ZIP_BOMB_MAX_BYTES = 100 * 1024 * 1024   # 100 MB descomprimidos
ZIP_BOMB_MAX_RATIO = 100                 # Razão máxima comprimido/descomprimido


def extrair_ip_cliente(req=None):
    """Extrai o IP real do cliente, respeitando proxies reversos (X-Forwarded-For)."""
    if req is None:
        try:
            from flask import request
            req = request
        except RuntimeError:
            return "127.0.0.1"
    if not req:
        return "127.0.0.1"
    xf = req.headers.get("X-Forwarded-For")
    if xf:
        return xf.split(",")[0].strip()
    return getattr(req, 'remote_addr', None) or "127.0.0.1"


def verificar_rate_limit(ip):
    agora = time.time()
    with _lock_rate:
        _contagem_ip[ip] = [t for t in _contagem_ip[ip] if agora - t < 60]
        if len(_contagem_ip[ip]) >= 60:
            return False
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
        session.permanent = True
    return session["csrf_token"]


def validar_csrf(tok=None):
    from flask import request
    if not tok and request:
        tok = (
            request.form.get("csrf_token") or
            request.headers.get("X-CSRFToken") or
            request.headers.get("X-CSRF-Token")
        )
        if not tok and request.is_json:
            try:
                tok = request.json.get("csrf_token")
            except Exception:
                pass

    sess_tok = session.get("csrf_token")
    if not sess_tok:
        session["csrf_token"] = secrets.token_hex(32)
        return True

    if not tok:
        return False

    return secrets.compare_digest(str(tok), str(sess_tok))


def csrf_required(f):
    from functools import wraps
    from flask import jsonify
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not validar_csrf():
            return jsonify({"sucesso": False, "erro": "Token CSRF inválido ou expirado."}), 400
        return f(*args, **kwargs)
    return decorated_function



_EXT_PERIGOSAS = {
    "exe", "bat", "cmd", "com", "php", "sh", "ps1", "vbs", "js",
    "jar", "py", "rb", "pl", "asp", "jsp", "cgi", "msi", "dll"
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


_EXPLICIT_EXECUTABLE_MAGIC = [
    b"MZ",                     # Windows PE Executable (.exe, .dll, .sys, .scr, .cpl)
    b"\x7fELF",                # Linux Executable (ELF)
    b"\xca\xfe\xba\xbe",        # Java Class File / Mach-O Fat Binary
    b"\xfe\xed\xfa\xce",        # Mach-O 32-bit (macOS)
    b"\xfe\xed\xfa\xcf",        # Mach-O 64-bit (macOS)
    b"\xce\xfa\xed\xfe",        # Mach-O 32-bit reverse (macOS)
    b"\xcf\xfa\xed\xfe",        # Mach-O 64-bit reverse (macOS)
    b"\x4d\x53\x43\x46",        # Microsoft CAB File (.cab)
]

_SCRIPT_TEXT_PATTERNS = [
    b"<?php",
    b"<script",
    b"#!/bin/sh",
    b"#!/bin/bash",
    b"#!/usr/bin/env",
    b"eval(base64_decode",
    b"wscript.shell",
    b"activexobject",
]


def verificar_assinatura_maliciosa(caminho: str) -> bool:
    """
    Varre os bytes iniciais do arquivo em busca de assinaturas maliciosas conhecidas.

    Returns:
        True se o arquivo for SUSPEITO/MALICIOSO (deve ser bloqueado);
        False se a varredura não encontrou nenhuma assinatura de risco.
    """
    try:
        with open(caminho, "rb") as f:
            header = f.read(512)

        if not header:
            return False

        # 1. Verifica magic bytes de executáveis binários
        for magic in _EXPLICIT_EXECUTABLE_MAGIC:
            if header.startswith(magic):
                return True

        # 2. Para scripts maliciosos embutidos
        header_lower = header.lower()
        for pat in _SCRIPT_TEXT_PATTERNS:
            if pat in header_lower:
                return True

        return False
    except Exception:
        return True


def validar_nome(nome):
    p = nome.split(".")
    if len(p) < 2:
        return True
    return not any(x.lower() in _EXT_PERIGOSAS for x in p[1:])


def validar_magic(caminho, ext):
    ext = (ext or "").lower()

    # 1. Bloqueia imediatamente se for identificado como assinatura de executável ou script malicioso
    if verificar_assinatura_maliciosa(caminho):
        return False

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


def validar_mime_type(request_file, extensoes_permitidas: set) -> bool:
    """
    Valida o Content-Type HTTP do arquivo enviado.
    Previne que um cliente envie um arquivo perigoso com Content-Type forjado.
    Esta validação é complementar à validação de magic bytes — ambas devem ser usadas.

    Args:
        request_file: Objeto FileStorage do Flask (request.files[...]).
        extensoes_permitidas: Set de extensões aceitas (ex: {'pdf', 'docx'}).

    Returns:
        True se o Content-Type é plausível para a extensão; False caso contrário.
    """
    MIME_ACEITOS = {
        "application/pdf", "application/octet-stream",
        "application/msword", "application/vnd.ms-excel",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "image/png", "image/jpeg", "image/webp", "image/heic", "image/gif",
        "video/mp4", "video/quicktime", "video/x-m4v",
        "audio/mpeg", "audio/mp3",
        "text/plain", "text/csv", "application/csv",
        "application/json", "text/json",
        "application/zip", "application/x-tar", "application/gzip",
        "application/x-zip-compressed", "multipart/x-zip",
        # Navegadores podem enviar tipos genéricos — sempre aceitar octet-stream
    }
    ct = (request_file.mimetype or "").lower().split(";")[0].strip()
    # Se Content-Type está ausente ou é genérico, permitir (será validado por magic bytes)
    if not ct or ct == "application/octet-stream":
        return True
    return ct in MIME_ACEITOS


def verificar_zip_bomb(caminho_zip: str) -> bool:
    """
    Verifica se um arquivo ZIP é uma Zip Bomb (arquivo comprimido armadilhado).

    Critérios de rejeição:
    - Tamanho total descomprimido > ZIP_BOMB_MAX_BYTES (padrão: 100 MB)
    - Razão comprimido/descomprimido > ZIP_BOMB_MAX_RATIO (padrão: 100x)

    Args:
        caminho_zip: Caminho para o arquivo ZIP a ser verificado.

    Returns:
        True se o arquivo é seguro; False se for suspeito de Zip Bomb.

    Raises:
        zipfile.BadZipFile: Se o arquivo não for um ZIP válido.
    """
    try:
        tamanho_zip = os.path.getsize(caminho_zip)
        total_descomprimido = 0

        with zipfile.ZipFile(caminho_zip, "r") as zf:
            for info in zf.infolist():
                total_descomprimido += info.file_size
                # Rejeita imediatamente se já passou do limite
                if total_descomprimido > ZIP_BOMB_MAX_BYTES:
                    return False

        # Verifica razão de compressão (evita 1GB comprimido para 1TB)
        if tamanho_zip > 0 and total_descomprimido > 0:
            ratio = total_descomprimido / tamanho_zip
            if ratio > ZIP_BOMB_MAX_RATIO:
                return False

        return True
    except zipfile.BadZipFile:
        # Não é um ZIP — deixa a validação de magic bytes lidar com isso
        return True
    except OSError:
        return False
