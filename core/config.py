"""config.py — Caminhos e constantes do aplicativo."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# PRISMA_DATA_DIR permite isolar os dados (usado pelos testes).
DATA_DIR = Path(os.environ.get("PRISMA_DATA_DIR") or BASE_DIR)
UPLOAD_DIR = DATA_DIR / "uploads"
DOWNLOAD_DIR = DATA_DIR / "downloads"
INSTANCE_DIR = DATA_DIR / "instance"

MAX_UPLOAD_BYTES = 20 * 1024 * 1024 * 1024  # 20 GB: só evita requisições absurdas
MAX_WORKERS = min(4, max(2, (os.cpu_count() or 2) // 2))

TIMEOUT_WORKER = 30 * 60
TIMEOUT_FFMPEG = 4 * 60 * 60
TIMEOUT_TRANSCRICAO = 6 * 60 * 60
TIMEOUT_PREVIEW = 90

POLITICAS_RETENCAO = {"instant": None, "5min": 300, "15min": 900}
POLITICA_PADRAO = "15min"
# Teto para arquivos de "download único" que nunca foram baixados.
LIMITE_SEM_DOWNLOAD = 60 * 60
RETENCAO_UPLOADS = 60 * 60
MAX_HISTORICO = 100

HOSTS_PERMITIDOS = {"127.0.0.1", "localhost"}


def garantir_pastas() -> None:
    for pasta in (UPLOAD_DIR, DOWNLOAD_DIR, INSTANCE_DIR):
        pasta.mkdir(parents=True, exist_ok=True)


def carregar_chave_secreta() -> str:
    """Lê a chave da instalação, gerando uma aleatória no primeiro uso."""
    env = (os.environ.get("SECRET_KEY") or "").strip()
    if env:
        return env
    garantir_pastas()
    arquivo = INSTANCE_DIR / "secret_key"
    if arquivo.exists():
        chave = arquivo.read_text(encoding="ascii").strip()
        if chave:
            return chave
    chave = secrets.token_hex(32)
    arquivo.write_text(chave, encoding="ascii")
    return chave
