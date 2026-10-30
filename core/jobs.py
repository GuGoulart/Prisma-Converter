"""jobs.py — Fila única de tarefas, com progresso, cancelamento e autodestruição dos resultados."""
import logging
import os
import shutil
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from core import config
from core.errors import ErroUsuario, JobCancelado
from core.processo import Controle
from core.tarefas import MSG_GENERICA
from core.utils import formatar_tamanho

log = logging.getLogger(__name__)

FILA, EXECUTANDO, CONCLUIDO, ERRO, CANCELADO = "fila", "executando", "concluido", "erro", "cancelado"
ATIVOS = {FILA, EXECUTANDO}


def _tamanho_legivel(caminho: str | None) -> str | None:
    try:
        return formatar_tamanho(os.path.getsize(caminho))
    except (OSError, TypeError):
        return None


def apagar(caminho: str | None) -> None:
    """Remove arquivo ou pasta. No Windows ele pode seguir aberto por instantes após o envio."""
    if not caminho:
        return
    for tentativa in range(5):
        try:
            if os.path.isdir(caminho):
                shutil.rmtree(caminho)
            elif os.path.exists(caminho):
                os.remove(caminho)
            return
        except OSError:
            if tentativa == 4:
                log.warning("Não foi possível apagar %s", caminho)
            time.sleep(0.3)


@dataclass
class Job:
    id: str
    nome_download: str = ""
    origem: str = ""
    destino: str = ""
    no_historico: bool = True
    politica: str = config.POLITICA_PADRAO
    status: str = FILA
    percent: float = 0.0
    erro: str | None = None
    aviso: str | None = None
    dados: dict | None = None
    caminho_saida: str | None = None
    pasta_entrada: str | None = None
    pasta_saida: str | None = None
    criado_em: float = field(default_factory=time.time)
    hora: str = field(default_factory=lambda: datetime.now().strftime("%H:%M"))
    expira_em: float | None = None
    limite_em: float | None = None
    apagado: bool = False
    renovado: bool = False
    controle: Controle = field(default_factory=Controle)

    def para_api(self) -> dict:
        pronto = self.status == CONCLUIDO and self.caminho_saida and not self.apagado
        return {
            "job_id": self.id,
            "status": self.status,
            "percent": round(self.percent, 1),
            "concluido": self.status not in ATIVOS,
            "erro": self.erro,
            "aviso": self.aviso,
            "dados": self.dados,
            "nome_download": self.nome_download,
            "tamanho": _tamanho_legivel(self.caminho_saida) if pronto else None,
            "download_url": f"/api/jobs/{self.id}/download" if pronto else None,
        }

    def para_historico(self) -> dict:
        return {
            "job_id": self.id,
            "nome": self.nome_download,
            "origem": self.origem,
            "destino": self.destino,
            "hora": self.hora,
            "autodestruicao": self.politica,
            "expira_em": int(self.expira_em) if self.expira_em else None,
            "apagado": self.apagado,
            "restaurado": self.renovado,
            "download_url": f"/api/jobs/{self.id}/download",
        }


class GerenciadorJobs:
    def __init__(self, workers: int = config.MAX_WORKERS):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="job")
        self._limpeza_iniciada = False

    # ── Ciclo de vida ──────────────────────────────────────────
    def criar(self, **campos) -> Job:
        job = Job(id=uuid.uuid4().hex, **campos)
        job.controle = Controle(lambda p: self._progresso(job, p), lambda m: self._avisar(job, m))
        with self._lock:
            self._jobs[job.id] = job
        return job

    def submeter(self, job: Job, trabalho: Callable[[Job], dict | None]) -> None:
        self._pool.submit(self._rodar, job, trabalho)

    def _rodar(self, job: Job, trabalho: Callable[[Job], dict | None]) -> None:
        erro = None
        retorno: dict = {}
        status = CONCLUIDO
        try:
            job.controle.verificar()
            job.status = EXECUTANDO
            retorno = trabalho(job) or {}
        except JobCancelado:
            status = CANCELADO
        except ErroUsuario as e:
            status, erro = ERRO, str(e)
        except Exception:
            log.exception("Job %s falhou", job.id[:8])
            status, erro = ERRO, MSG_GENERICA

        # A limpeza vem antes de publicar o status: quem vê "concluído" já encontra tudo em ordem.
        apagar(job.pasta_entrada)
        if status != CONCLUIDO:
            apagar(job.pasta_saida)
        with self._lock:
            if status == CONCLUIDO:
                job.dados = retorno.get("dados")
                job.nome_download = retorno.get("nome_download") or job.nome_download
                job.caminho_saida = retorno.get("caminho") or job.caminho_saida
                job.percent = 100.0
                agora = time.time()
                ttl = config.POLITICAS_RETENCAO.get(job.politica)
                job.expira_em = agora + ttl if ttl else None
                job.limite_em = agora + (ttl or config.LIMITE_SEM_DOWNLOAD)
            else:
                job.caminho_saida = None
            job.erro = erro
            job.status = status

    def _progresso(self, job: Job, percent: float) -> None:
        job.percent = max(job.percent, min(percent, 99.0))

    def _avisar(self, job: Job, mensagem: str) -> None:
        job.aviso = mensagem

    # ── Consultas e ações ──────────────────────────────────────
    def obter(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def cancelar(self, job_id: str) -> bool:
        job = self.obter(job_id)
        if not job or job.status not in ATIVOS:
            return False
        job.controle.cancelar()
        return True

    def historico(self) -> list[dict]:
        with self._lock:
            itens = [j for j in self._jobs.values() if j.no_historico and j.status == CONCLUIDO]
        itens.sort(key=lambda j: j.criado_em, reverse=True)
        return [j.para_historico() for j in itens[: config.MAX_HISTORICO]]

    def arquivos_ativos(self) -> list[Job]:
        with self._lock:
            return [j for j in self._jobs.values()
                    if j.no_historico and j.status == CONCLUIDO and not j.apagado
                    and j.caminho_saida and os.path.exists(j.caminho_saida)]

    def tem_trabalho_ativo(self) -> bool:
        with self._lock:
            return any(j.status in ATIVOS for j in self._jobs.values())

    def pastas_em_uso(self) -> set[str]:
        with self._lock:
            return {os.path.normcase(os.path.abspath(p)) for j in self._jobs.values()
                    if j.status in ATIVOS for p in (j.pasta_entrada, j.pasta_saida) if p}

    def renovar(self, job_id: str) -> Job | None:
        job = self.obter(job_id)
        if not job or job.apagado or job.status != CONCLUIDO:
            return None
        ttl = config.POLITICAS_RETENCAO.get(job.politica)
        if not ttl:
            return None
        with self._lock:
            job.expira_em = job.limite_em = time.time() + ttl
            job.renovado = True
        return job

    def destruir(self, job: Job) -> None:
        """Apaga o resultado e mantém a linha no histórico."""
        with self._lock:
            job.apagado = True
            job.expira_em = None
            caminho, job.caminho_saida = job.caminho_saida, None
            pasta = job.pasta_saida
        apagar(pasta or caminho)

    def destruir_todos(self) -> int:
        with self._lock:
            alvos = [j for j in self._jobs.values() if j.status == CONCLUIDO and not j.apagado]
        for job in alvos:
            self.destruir(job)
        return len(alvos)

    # ── Limpeza ────────────────────────────────────────────────
    def iniciar_limpeza(self) -> None:
        if self._limpeza_iniciada:
            return
        self._limpeza_iniciada = True
        threading.Thread(target=self._loop_limpeza, daemon=True, name="limpeza").start()

    def _loop_limpeza(self) -> None:
        while True:
            time.sleep(15)
            try:
                self.limpar_expirados()
                self.limpar_uploads_antigos()
            except Exception:
                log.exception("Erro na limpeza")

    def limpar_expirados(self, agora: float | None = None) -> None:
        agora = agora or time.time()
        with self._lock:
            vencidos = [j for j in self._jobs.values()
                        if j.status == CONCLUIDO and not j.apagado and j.limite_em and j.limite_em <= agora]
            antigos = [j.id for j in self._jobs.values()
                       if j.status not in ATIVOS and not j.no_historico and agora - j.criado_em > 3600]
            for jid in antigos:
                self._jobs.pop(jid, None)
        for job in vencidos:
            self.destruir(job)

    def limpar_uploads_antigos(self, agora: float | None = None) -> None:
        agora = agora or time.time()
        em_uso = self.pastas_em_uso()
        if not config.UPLOAD_DIR.exists():
            return
        for item in config.UPLOAD_DIR.iterdir():
            try:
                if (os.path.normcase(os.path.abspath(item)) not in em_uso
                        and agora - item.stat().st_mtime > config.RETENCAO_UPLOADS):
                    apagar(str(item))
            except OSError:
                pass

    def limpar_tudo_na_inicializacao(self) -> None:
        """Sem jobs em memória, tudo que restou de uma execução anterior é órfão."""
        for pasta in (config.UPLOAD_DIR, config.DOWNLOAD_DIR):
            if pasta.exists():
                for item in pasta.iterdir():
                    apagar(str(item))


jobs = GerenciadorJobs()
