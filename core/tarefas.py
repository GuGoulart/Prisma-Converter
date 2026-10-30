"""tarefas.py — Dispara core.worker em um subprocesso e acompanha o resultado."""
import json
import logging
import os
import sys

from core.config import BASE_DIR, TIMEOUT_WORKER
from core.errors import ErroUsuario
from core.processo import Controle, TempoEsgotado, executar

log = logging.getLogger(__name__)
MSG_GENERICA = "Não foi possível concluir a operação. O arquivo pode estar corrompido ou não ser suportado."


def executar_tarefa(tarefa: str, *args, controle: Controle | None = None,
                    timeout: float = TIMEOUT_WORKER, **kwargs):
    """Roda uma tarefa de core.worker. Retorna o valor ou lança ErroUsuario/JobCancelado."""
    controle = controle or Controle()
    resposta: dict = {}

    def _linha(linha: str):
        if linha.startswith("@@PROGRESSO "):
            controle.ao_progredir(float(linha.split(" ", 1)[1]))
        elif linha.startswith("@@AVISO "):
            controle.ao_avisar(linha.split(" ", 1)[1])
        elif linha.startswith("@@RESULTADO "):
            resposta.update(json.loads(linha.split(" ", 1)[1]))

    env = {**os.environ, "PRISMA_WORKER": "1", "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    pedido = json.dumps({"tarefa": tarefa, "args": args, "kwargs": kwargs}, ensure_ascii=False)
    try:
        r = executar([sys.executable, "-m", "core.worker"], controle, timeout=timeout,
                     stdin_texto=pedido, ao_linha=_linha, cwd=str(BASE_DIR), env=env)
    except TempoEsgotado:
        raise ErroUsuario("A operação demorou demais e foi interrompida. Tente um arquivo menor.") from None

    if resposta.get("ok"):
        return resposta.get("valor")
    if resposta.get("erro"):
        raise ErroUsuario(resposta["erro"])
    log.error("Tarefa %s falhou (código %s): %s", tarefa, r.codigo, r.stderr[-2000:])
    raise ErroUsuario(MSG_GENERICA)
