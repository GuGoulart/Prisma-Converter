"""progresso.py — Canal entre o processo worker e o job que o acompanha."""
import os

_ATIVO = os.environ.get("PRISMA_WORKER") == "1"


def reportar(percent: float) -> None:
    if _ATIVO:
        print(f"@@PROGRESSO {float(percent):.1f}", flush=True)


def avisar(mensagem: str) -> None:
    if _ATIVO:
        print("@@AVISO " + mensagem.replace("\n", " "), flush=True)
