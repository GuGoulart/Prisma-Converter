"""
tasks.py — Sistema de tarefas assíncronas para conversões pesadas.

Modo de operação (selecionado automaticamente):
─────────────────────────────────────────────────────────────────────────────
• Sem REDIS_URL → tarefas executam em threads do processo (sem infra extra).
  Comportamento idêntico ao atual + rastreamento de status por job_id.
  Adequado para uso individual e Cloud Run com instância única.

• Com REDIS_URL → tarefas são enviadas ao Celery com broker Redis.
  Permite múltiplos workers, retry automático e persistência de estado.
  Adequado para produção com alto volume de requisições.
─────────────────────────────────────────────────────────────────────────────

Uso:
    from core.tasks import job_store, executar_conversao_async

    job_id = executar_conversao_async(
        entrada=..., saida=..., origem=..., destino=...,
        orientacao=..., nome_original=..., pasta_uid=...
    )
    # Retorna imediatamente — a conversão roda em background.

    job = job_store.get(job_id)
    # job["percent"] — progresso 0-100
    # job["status"]  — mensagem descritiva
    # job["concluido"] — True quando finalizado
    # job["erro"]    — mensagem de erro (None se OK)
    # job["caminho_saida"] — caminho do arquivo gerado
"""

import os
import time
import uuid
import threading
import logging

log = logging.getLogger(__name__)

# ─── Configuração de modo (Celery vs Thread) ─────────────────────────────────

REDIS_URL = (os.environ.get("REDIS_URL") or "").strip()
_USE_CELERY = False
celery_app = None

if REDIS_URL:
    try:
        from celery import Celery

        celery_app = Celery(
            "prisma",
            broker=REDIS_URL,
            backend=REDIS_URL,
            include=["core.tasks"],
        )
        celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="UTC",
            enable_utc=True,
            task_track_started=True,
            worker_prefetch_multiplier=1,
            task_acks_late=True,
            task_reject_on_worker_lost=True,
            # Expirar resultados após 1 hora
            result_expires=3600,
        )
        _USE_CELERY = True
        log.info("[tasks] Modo: Celery com Redis (%s)", REDIS_URL[:30] + "...")
    except ImportError:
        log.warning("[tasks] celery não instalado — usando modo thread.")
else:
    log.info("[tasks] Modo: thread em processo (sem REDIS_URL configurado).")


# ─── Job Store (armazenamento de estado em memória) ───────────────────────────

class _JobStore:
    """
    Dicionário thread-safe de jobs de conversão.

    Cada job tem o formato:
        {
            "percent":       float,   # 0.0 – 100.0
            "status":        str,     # descrição legível
            "concluido":     bool,
            "erro":          str|None,
            "caminho_saida": str|None,  # path do arquivo gerado
            "pasta_uid":     str,       # uuid da pasta de upload
            "nome_download": str,       # nome sugerido para download
            "timestamp":     float,     # epoch de criação
        }

    Jobs expiram automaticamente após TTL (padrão: 30 minutos).
    """

    TTL = 30 * 60  # 30 minutos

    def __init__(self):
        self._store: dict[str, dict] = {}
        self._lock = threading.Lock()
        # Iniciar thread de limpeza de jobs expirados
        t = threading.Thread(target=self._limpeza_loop, daemon=True)
        t.start()

    def criar(self, job_id: str, pasta_uid: str, nome_download: str, autodestruicao: str = "15min", origem: str = "", destino: str = "", tamanho_original: int | None = None) -> dict:
        if autodestruicao not in ("instant", "5min", "15min"):
            autodestruicao = "15min"
        job = {
            "percent": 0.0,
            "status": "Aguardando processamento...",
            "concluido": False,
            "erro": None,
            "caminho_saida": None,
            "pasta_uid": pasta_uid,
            "nome_download": nome_download,
            "autodestruicao": autodestruicao,
            "origem": origem,
            "destino": destino,
            "tamanho_original": tamanho_original,
            "timestamp": time.time(),
        }
        with self._lock:
            self._store[job_id] = job
        return job

    def get(self, job_id: str) -> dict | None:
        with self._lock:
            return self._store.get(job_id)

    def atualizar(self, job_id: str, **kwargs):
        with self._lock:
            if job_id in self._store:
                self._store[job_id].update(kwargs)

    def remover(self, job_id: str):
        with self._lock:
            self._store.pop(job_id, None)

    def renovar_expiracao(self, job_id: str) -> bool:
        """Reinicia o timestamp de criação do job para estender sua retenção."""
        with self._lock:
            if job_id in self._store:
                self._store[job_id]["timestamp"] = time.time()
                return True
            return False

    def _limpeza_loop(self):
        """Remove jobs e arquivos expirados conforme a política de autodestruição."""
        from core.storage import storage
        while True:
            time.sleep(30)
            agora = time.time()
            with self._lock:
                expirados = []
                for jid, j in list(self._store.items()):
                    politica = j.get("autodestruicao", "15min")
                    tempo_decorrido = agora - j["timestamp"]
                    # 5 min (300s) ou 15 min (900s) / fallback TTL 30 min
                    limite = 300 if politica == "5min" else (900 if politica == "15min" else self.TTL)
                    if tempo_decorrido > limite:
                        expirados.append((jid, j.get("caminho_saida"), j.get("pasta_uid")))

                for jid, caminho_saida, pasta_uid in expirados:
                    self._store.pop(jid, None)
                    if caminho_saida:
                        try:
                            storage.remover(caminho_saida)
                        except Exception:
                            pass
                    if pasta_uid:
                        try:
                            from core.cleanup import _remover_item_seguro
                            pasta = os.path.join("uploads", pasta_uid)
                            if os.path.exists(pasta):
                                _remover_item_seguro(pasta)
                        except Exception:
                            pass
            if expirados:
                log.info("[tasks] Autodestruição: %d jobs/arquivos removidos por expiração", len(expirados))


# Instância global do job store
job_store = _JobStore()


# ─── Função de conversão (executada pelo worker ou pela thread) ───────────────

def _executar_conversao(
    job_id: str,
    entrada: str,
    saida: str,
    origem: str,
    destino: str,
    orientacao: str,
):
    """
    Executa a conversão de arquivo e atualiza o job_store com o progresso.
    Esta função é chamada tanto pelo executor em thread quanto pelo Celery.
    """
    from core.converter import converter_arquivo

    try:
        log.info("[tasks:%s] Iniciando: %s->%s (%s)", job_id[:8], origem, destino, os.path.basename(entrada))
        job_store.atualizar(job_id, percent=10.0, status="Preparando conversão...")

        # Conversão principal (bloqueante)
        converter_arquivo(entrada, saida, origem, destino, orientacao=orientacao)

        if not os.path.exists(saida) or os.path.getsize(saida) == 0:
            raise RuntimeError("Arquivo de saída não foi gerado ou está vazio.")

        job_store.atualizar(
            job_id,
            percent=100.0,
            status="Conversão concluída!",
            concluido=True,
            caminho_saida=saida,
        )
        log.info("[tasks:%s] Concluído: %s", job_id[:8], os.path.basename(saida))

    except Exception as e:
        import traceback
        log.error("[tasks:%s] Erro: %s\n%s", job_id[:8], e, traceback.format_exc())
        job_store.atualizar(
            job_id,
            percent=0.0,
            status="Erro na conversão.",
            concluido=True,  # CRÍTICO: sinaliza fim para o cliente parar o polling
            erro=str(e),
        )


# ─── Tarefa Celery (opcional) ─────────────────────────────────────────────────

if _USE_CELERY and celery_app is not None:
    @celery_app.task(name="core.tasks.tarefa_converter", bind=True, max_retries=1)
    def tarefa_converter(self, job_id, entrada, saida, origem, destino, orientacao):
        """Tarefa Celery para conversão assíncrona."""
        _executar_conversao(job_id, entrada, saida, origem, destino, orientacao)


# ─── API pública ──────────────────────────────────────────────────────────────

def executar_conversao_async(
    entrada: str,
    saida: str,
    origem: str,
    destino: str,
    orientacao: str,
    pasta_uid: str,
    nome_download: str,
    timeout_segundos: int = 120,
    autodestruicao: str = "15min",
    tamanho_original: int | None = None,
) -> str:
    """
    Enfileira ou inicia a conversão de arquivo de forma assíncrona.

    Args:
        entrada:         Caminho do arquivo de entrada.
        saida:           Caminho do arquivo de saída.
        origem:          Extensão de origem (ex: "pdf").
        destino:         Extensão de destino (ex: "docx").
        orientacao:      "retrato" ou "paisagem".
        pasta_uid:       UUID da pasta de upload (para limpeza posterior).
        nome_download:   Nome sugerido para o arquivo baixado.
        timeout_segundos: Máximo de segundos para execução (modo thread).
        autodestruicao:  Política de retenção ("instant", "5min", "15min").

    Returns:
        job_id: Identificador único do job — use para consultar o status.
    """
    job_id = uuid.uuid4().hex
    job_store.criar(
        job_id, pasta_uid, nome_download, autodestruicao=autodestruicao,
        origem=origem, destino=destino, tamanho_original=tamanho_original,
    )

    if _USE_CELERY and celery_app is not None:
        # Modo Celery: envia para a fila
        tarefa_converter.apply_async(
            args=[job_id, entrada, saida, origem, destino, orientacao],
            expires=timeout_segundos + 30,
        )
        log.info("[tasks] Job %s enviado ao Celery.", job_id[:8])
    else:
        # Modo thread: executa no processo atual (com timeout via thread daemon)
        def _worker():
            _executar_conversao(job_id, entrada, saida, origem, destino, orientacao)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

        # Timeout watchdog: marca o job como erro se exceder o tempo
        def _watchdog():
            t.join(timeout=timeout_segundos)
            if t.is_alive():
                log.warning("[tasks] Timeout (%ds) para job %s", timeout_segundos, job_id[:8])
                job_store.atualizar(
                    job_id,
                    percent=0.0,
                    status="Tempo de conversão excedido.",
                    concluido=True,  # CRÍTICO: sinaliza fim para o cliente parar o polling
                    erro="A conversão demorou mais do que o esperado. Tente um arquivo menor.",
                )

        threading.Thread(target=_watchdog, daemon=True).start()
        log.info("[tasks] Job %s iniciado em thread.", job_id[:8])

    return job_id
