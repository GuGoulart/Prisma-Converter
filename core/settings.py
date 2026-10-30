"""settings.py — Preferências do usuário, persistidas em disco."""
import json
import threading

from core import config

_lock = threading.Lock()


def _arquivo():
    return config.INSTANCE_DIR / "settings.json"


def _ler() -> dict:
    try:
        return json.loads(_arquivo().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def politica_retencao() -> str:
    politica = _ler().get("politica_retencao")
    return politica if politica in config.POLITICAS_RETENCAO else config.POLITICA_PADRAO


def definir_politica_retencao(politica: str) -> str:
    if politica not in config.POLITICAS_RETENCAO:
        politica = config.POLITICA_PADRAO
    with _lock:
        dados = _ler()
        dados["politica_retencao"] = politica
        config.garantir_pastas()
        _arquivo().write_text(json.dumps(dados), encoding="utf-8")
    return politica
