"""
storage.py — Backend de armazenamento abstrato (local + Google Cloud Storage).

Modo de operação (selecionado automaticamente):
─────────────────────────────────────────────────────────────────────────────
• Sem GCS_BUCKET ou sem credenciais -> armazenamento local em disco.
• Com GCS_BUCKET válido e credenciais -> arquivos salvos no Google Cloud Storage.
─────────────────────────────────────────────────────────────────────────────
"""

import os
import io
import logging

log = logging.getLogger(__name__)

GCS_BUCKET = (os.environ.get("GCS_BUCKET") or "").strip()
GCS_PREFIX = (os.environ.get("GCS_PREFIX") or "").strip() or "prisma/"
_USE_GCS = False
_gcs_client = None
_gcs_bucket_obj = None

if GCS_BUCKET:
    try:
        from google.cloud import storage as gcs_lib
        _gcs_client = gcs_lib.Client()
        _gcs_bucket_obj = _gcs_client.bucket(GCS_BUCKET)
        _USE_GCS = True
        log.info("[storage] Modo: Google Cloud Storage — bucket '%s'", GCS_BUCKET)
    except ImportError:
        log.warning("[storage] google-cloud-storage não instalado — usando armazenamento local.")
        _USE_GCS = False
    except Exception as e:
        log.warning("[storage] Não foi possível autenticar no GCS (%s) — usando armazenamento local.", e)
        _USE_GCS = False


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


class _GCSStorageBackend:
    def __init__(self):
        self._local_fallback = _LocalStorageBackend()

    def salvar(self, caminho_local: str, nome: str = None) -> str:
        if not _gcs_bucket_obj:
            return self._local_fallback.salvar(caminho_local, nome)

        if nome is None:
            nome = os.path.basename(caminho_local)

        gcs_path = GCS_PREFIX + nome

        try:
            blob = _gcs_bucket_obj.blob(gcs_path)
            blob.upload_from_filename(caminho_local)
            log.info("[storage:gcs] Upload OK: gs://%s/%s", GCS_BUCKET, gcs_path)
            try:
                os.remove(caminho_local)
            except OSError:
                pass
            return f"gs://{GCS_BUCKET}/{gcs_path}"
        except Exception as e:
            log.warning("[storage:gcs] Erro no upload (%s) — salvando localmente.", e)
            return self._local_fallback.salvar(caminho_local, nome)

    def ler(self, gcs_uri: str) -> bytes:
        if not _gcs_bucket_obj or not gcs_uri.startswith("gs://"):
            return self._local_fallback.ler(gcs_uri)
        try:
            blob = _gcs_bucket_obj.blob(self._extrair_path(gcs_uri))
            buf = io.BytesIO()
            blob.download_to_file(buf)
            buf.seek(0)
            return buf.read()
        except Exception as e:
            log.warning("[storage:gcs] Erro ao ler GCS (%s) — tentando leitura local.", e)
            return self._local_fallback.ler(gcs_uri)

    def remover(self, gcs_uri: str, modo_seguro: bool = True):
        if not _gcs_bucket_obj or not gcs_uri.startswith("gs://"):
            return self._local_fallback.remover(gcs_uri, modo_seguro=modo_seguro)
        try:
            blob = _gcs_bucket_obj.blob(self._extrair_path(gcs_uri))
            blob.delete()
            log.debug("[storage:gcs] Removido: %s", gcs_uri)
        except Exception as e:
            log.warning("[storage:gcs] Erro ao remover GCS (%s) — usando remoção local.", e)
            self._local_fallback.remover(gcs_uri, modo_seguro=modo_seguro)

    def existe(self, gcs_uri: str) -> bool:
        if not _gcs_bucket_obj or not gcs_uri.startswith("gs://"):
            return self._local_fallback.existe(gcs_uri)
        try:
            return _gcs_bucket_obj.blob(self._extrair_path(gcs_uri)).exists()
        except Exception:
            return self._local_fallback.existe(gcs_uri)

    def gerar_url_temporaria(self, gcs_uri: str, expira_segundos: int = 3600) -> str | None:
        if not _gcs_bucket_obj or not gcs_uri.startswith("gs://"):
            return None
        try:
            from datetime import timedelta
            blob = _gcs_bucket_obj.blob(self._extrair_path(gcs_uri))
            return blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expira_segundos),
                method="GET",
            )
        except Exception as e:
            log.warning("[storage:gcs] Não foi possível gerar URL assinada: %s", e)
            return None

    def _extrair_path(self, gcs_uri: str) -> str:
        if gcs_uri.startswith("gs://"):
            partes = gcs_uri[5:].split("/", 1)
            return partes[1] if len(partes) > 1 else ""
        return gcs_uri

    def __repr__(self):
        return f"<GCSStorageBackend bucket='{GCS_BUCKET}'>"


# ─── Instância global com Fallback Automático e Seguro ────────────────────────
storage = _GCSStorageBackend() if (_USE_GCS and _gcs_bucket_obj is not None) else _LocalStorageBackend()
