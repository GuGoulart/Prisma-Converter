"""
storage.py — Backend de armazenamento abstrato (local + Google Cloud Storage).

Modo de operação (selecionado automaticamente):
─────────────────────────────────────────────────────────────────────────────
• Sem GCS_BUCKET → armazenamento local em disco.
  Adequado para desenvolvimento, execução local e Cloud Run simples.
  ATENÇÃO: O disco do Cloud Run é efêmero — arquivos são perdidos em restarts.

• Com GCS_BUCKET → arquivos enviados ao Google Cloud Storage.
  Adequado para produção com múltiplas réplicas no Cloud Run.
  Requer que a Service Account do Cloud Run tenha papel "Storage Object Admin".

Variáveis de ambiente:
    GCS_BUCKET      — Nome do bucket GCS (ex: "prisma-uploads-prod")
    GCS_PREFIX      — Prefixo de pasta no bucket (padrão: "prisma/")
─────────────────────────────────────────────────────────────────────────────

Uso:
    from core.storage import storage

    # Salvar arquivo (retorna caminho local ou URL GCS)
    path = storage.salvar(caminho_local, nome_arquivo)

    # Ler arquivo (retorna bytes)
    dados = storage.ler(path)

    # Remover arquivo
    storage.remover(path)

    # Verificar se existe
    existe = storage.existe(path)
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
    except Exception as e:
        log.error("[storage] Erro ao inicializar GCS: %s — usando armazenamento local.", e)
else:
    log.info("[storage] Modo: armazenamento local em disco.")


class _LocalStorageBackend:
    """
    Backend de armazenamento local — usa o disco do servidor.
    Simples e sem dependências externas.
    """

    def salvar(self, caminho_local: str, _nome: str = None) -> str:
        """Arquivo já está no disco — retorna o caminho como-está."""
        return caminho_local

    def ler(self, caminho: str) -> bytes:
        """Lê bytes de um arquivo local."""
        with open(caminho, "rb") as f:
            return f.read()

    def remover(self, caminho: str):
        """Remove um arquivo local."""
        try:
            if os.path.exists(caminho):
                os.remove(caminho)
        except OSError as e:
            log.warning("[storage:local] Erro ao remover %s: %s", caminho, e)

    def existe(self, caminho: str) -> bool:
        """Verifica se um arquivo local existe."""
        return os.path.exists(caminho)

    def gerar_url_temporaria(self, caminho: str, _expira_segundos: int = 3600) -> str | None:
        """Storage local não gera URLs temporárias — retorna None."""
        return None

    def __repr__(self):
        return "<LocalStorageBackend>"


class _GCSStorageBackend:
    """
    Backend de armazenamento no Google Cloud Storage.
    Os arquivos são enviados ao GCS e removidos do disco local após o upload.

    Nota: Para Cloud Run, as credenciais são obtidas automaticamente via
    Workload Identity ou Application Default Credentials (ADC).
    """

    def salvar(self, caminho_local: str, nome: str = None) -> str:
        """
        Faz upload de um arquivo local para o GCS e retorna o path no bucket.
        O arquivo local é removido após o upload bem-sucedido.
        """
        if nome is None:
            nome = os.path.basename(caminho_local)

        gcs_path = GCS_PREFIX + nome

        try:
            blob = _gcs_bucket_obj.blob(gcs_path)
            blob.upload_from_filename(caminho_local)
            log.info("[storage:gcs] Upload OK: gs://%s/%s", GCS_BUCKET, gcs_path)
            # Remove o arquivo local após upload bem-sucedido
            try:
                os.remove(caminho_local)
            except OSError:
                pass
            return f"gs://{GCS_BUCKET}/{gcs_path}"
        except Exception as e:
            log.error("[storage:gcs] Erro no upload: %s", e)
            raise RuntimeError(f"Erro ao salvar arquivo no Cloud Storage: {e}") from e

    def ler(self, gcs_uri: str) -> bytes:
        """Lê bytes de um arquivo no GCS a partir da URI gs://..."""
        try:
            blob = _gcs_bucket_obj.blob(self._extrair_path(gcs_uri))
            buf = io.BytesIO()
            blob.download_to_file(buf)
            buf.seek(0)
            return buf.read()
        except Exception as e:
            log.error("[storage:gcs] Erro ao ler: %s — %s", gcs_uri, e)
            raise

    def remover(self, gcs_uri: str):
        """Remove um arquivo do GCS."""
        try:
            blob = _gcs_bucket_obj.blob(self._extrair_path(gcs_uri))
            blob.delete()
            log.debug("[storage:gcs] Removido: %s", gcs_uri)
        except Exception as e:
            log.warning("[storage:gcs] Erro ao remover %s: %s", gcs_uri, e)

    def existe(self, gcs_uri: str) -> bool:
        """Verifica se um arquivo existe no GCS."""
        try:
            return _gcs_bucket_obj.blob(self._extrair_path(gcs_uri)).exists()
        except Exception:
            return False

    def gerar_url_temporaria(self, gcs_uri: str, expira_segundos: int = 3600) -> str | None:
        """
        Gera uma Signed URL temporária para download direto do GCS.
        Requer que a Service Account tenha permissão "iam.serviceAccounts.signBlob".
        """
        try:
            from datetime import timedelta
            blob = _gcs_bucket_obj.blob(self._extrair_path(gcs_uri))
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expira_segundos),
                method="GET",
            )
            return url
        except Exception as e:
            log.warning("[storage:gcs] Não foi possível gerar URL assinada: %s", e)
            return None

    def _extrair_path(self, gcs_uri: str) -> str:
        """Extrai o path do objeto a partir de gs://bucket/path."""
        if gcs_uri.startswith("gs://"):
            # gs://bucket-name/path/to/file → path/to/file
            partes = gcs_uri[5:].split("/", 1)
            return partes[1] if len(partes) > 1 else ""
        return gcs_uri

    def __repr__(self):
        return f"<GCSStorageBackend bucket='{GCS_BUCKET}'>"


# ─── Instância global ─────────────────────────────────────────────────────────

storage = _GCSStorageBackend() if _USE_GCS else _LocalStorageBackend()
