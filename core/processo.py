"""processo.py — Subprocessos que podem ser cancelados e encerrados por tempo."""
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable

from core.errors import JobCancelado

log = logging.getLogger(__name__)
_SEM_JANELA = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


class Controle:
    """Estado compartilhado entre o job e o trabalho que ele executa."""

    def __init__(self, ao_progredir: Callable[[float], None] | None = None,
                 ao_avisar: Callable[[str], None] | None = None):
        self._cancelado = threading.Event()
        self.ao_progredir = ao_progredir or (lambda _p: None)
        self.ao_avisar = ao_avisar or (lambda _m: None)

    def cancelar(self) -> None:
        self._cancelado.set()

    @property
    def cancelado(self) -> bool:
        return self._cancelado.is_set()

    def verificar(self) -> None:
        if self.cancelado:
            raise JobCancelado()


@dataclass
class Resultado:
    codigo: int
    stderr: str


class TempoEsgotado(Exception):
    pass


def _encerrar_arvore(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                           capture_output=True, creationflags=_SEM_JANELA, timeout=15)
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except (OSError, subprocess.SubprocessError) as e:
        log.warning("Falha ao encerrar árvore do processo %s: %s", proc.pid, e)
        proc.kill()


def executar(cmd: list[str], controle: Controle | None = None, timeout: float | None = None,
             stdin_texto: str | None = None, ao_linha: Callable[[str], None] | None = None,
             cwd: str | None = None, env: dict | None = None) -> Resultado:
    """Executa `cmd`, repassando cada linha do stdout para `ao_linha`.

    Lança JobCancelado ou TempoEsgotado depois de encerrar o processo e seus filhos.
    """
    controle = controle or Controle()
    kwargs = {"start_new_session": True} if sys.platform != "win32" else {"creationflags": _SEM_JANELA}
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE if stdin_texto is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding="utf-8", errors="replace", cwd=cwd, env=env, **kwargs,
    )
    fim_stderr: deque[str] = deque(maxlen=200)

    def _ler_stderr():
        for linha in proc.stderr:
            fim_stderr.append(linha)

    def _ler_stdout():
        for linha in proc.stdout:
            if ao_linha:
                try:
                    ao_linha(linha.rstrip("\r\n"))
                except Exception:
                    log.exception("Erro ao tratar linha do subprocesso")

    leitores = [threading.Thread(target=_ler_stderr, daemon=True),
                threading.Thread(target=_ler_stdout, daemon=True)]
    for t in leitores:
        t.start()

    if stdin_texto is not None:
        try:
            proc.stdin.write(stdin_texto)
            proc.stdin.close()
        except OSError:
            pass

    limite = time.monotonic() + timeout if timeout else None
    while proc.poll() is None:
        if controle.cancelado:
            _encerrar_arvore(proc)
            proc.wait()
            raise JobCancelado()
        if limite and time.monotonic() > limite:
            _encerrar_arvore(proc)
            proc.wait()
            raise TempoEsgotado()
        time.sleep(0.1)

    for t in leitores:
        t.join(timeout=5)
    return Resultado(proc.returncode, "".join(fim_stderr))
