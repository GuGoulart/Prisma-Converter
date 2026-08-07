"""
storage.py — Backend de armazenamento local para o Render.

Todos os arquivos são armazenados em disco no próprio servidor.
O Render usa discos efêmeros por padrão; configure um Render Disk
persistente se precisar de retenção entre deploys.
"""

import os
import logging

log = logging.getLogger(__name__)


class _LocalStorageBackend:
    def salvar(self, caminho_local: str, _nome: str = None) -> str:
        return caminho_local

    def ler(self, caminho: str) -> bytes:
        with open(caminho, "rb") as f:
            return f.read()

    def remover(self, caminho: str, modo_seguro: bool = True):
        try:
            if os.path.exists(caminho):
                if modo_seguro:
                    try:
                        sz = os.path.getsize(caminho)
                        with open(caminho, "r+b") as f:
                            f.write(b"\x00" * sz)
                            f.flush()
                            os.fsync(f.fileno())
                    except Exception as ex:
                        log.warning("[storage:local] Falha ao sobrescrever bytes em %s: %s", caminho, ex)
                os.remove(caminho)
        except OSError as e:
            log.warning("[storage:local] Erro ao remover %s: %s", caminho, e)

    def existe(self, caminho: str) -> bool:
        return os.path.exists(caminho)

    def gerar_url_temporaria(self, caminho: str, _expira_segundos: int = 3600) -> str | None:
        return None

    def __repr__(self):
        return "<LocalStorageBackend>"


# ─── Instância global ─────────────────────────────────────────────────────────
storage = _LocalStorageBackend()
log.info("[storage] Modo: armazenamento local em disco.")
