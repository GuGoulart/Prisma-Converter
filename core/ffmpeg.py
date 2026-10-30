"""ffmpeg.py — Execução do FFmpeg/ffprobe com progresso real e erros legíveis."""
import logging
import os
import shutil
import threading

from core.config import TIMEOUT_FFMPEG
from core.errors import ErroUsuario
from core.processo import Controle, TempoEsgotado, executar

log = logging.getLogger(__name__)


def preparar_ffmpeg() -> None:
    """Sem FFmpeg no PATH, usa o binário do static-ffmpeg (que baixa no primeiro uso)."""
    def _tarefa():
        try:
            if not shutil.which("ffmpeg"):
                import static_ffmpeg
                static_ffmpeg.add_paths()
        except Exception as e:
            log.warning("FFmpeg estático indisponível: %s", e)
    threading.Thread(target=_tarefa, daemon=True, name="ffmpeg-setup").start()


def ffmpeg_disponivel() -> bool:
    return shutil.which("ffmpeg") is not None


def obter_duracao(caminho: str) -> float:
    """Duração em segundos, ou 0.0 quando não é possível determinar."""
    if not shutil.which("ffprobe"):
        return 0.0
    linhas: list[str] = []
    try:
        r = executar(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "default=noprint_wrappers=1:nokey=1", caminho],
                     timeout=30, ao_linha=linhas.append)
        return float(linhas[0]) if r.codigo == 0 and linhas else 0.0
    except (ValueError, IndexError, TempoEsgotado, OSError):
        return 0.0


def rodar_ffmpeg(args: list[str], controle: Controle | None = None, duracao: float = 0.0,
                 timeout: float = TIMEOUT_FFMPEG, saida: str | None = None) -> None:
    """Executa o FFmpeg e lança ErroUsuario em caso de falha."""
    if not ffmpeg_disponivel():
        raise ErroUsuario("FFmpeg não encontrado. Instale o FFmpeg e reinicie o Prisma.")
    controle = controle or Controle()

    def _linha(linha: str):
        if duracao > 0 and linha.startswith("out_time_us="):
            try:
                controle.ao_progredir(min(99.0, int(linha.split("=", 1)[1]) / 1_000_000 / duracao * 100))
            except ValueError:
                pass

    cmd = ["ffmpeg", "-y", "-nostdin", "-hide_banner", "-loglevel", "error", "-progress", "pipe:1", *args]
    log.debug("ffmpeg: %s", cmd)
    try:
        r = executar(cmd, controle, timeout=timeout, ao_linha=_linha)
    except TempoEsgotado:
        raise ErroUsuario("O processamento demorou demais e foi interrompido.") from None
    if r.codigo != 0:
        log.error("FFmpeg falhou (%s): %s", r.codigo, r.stderr[-1500:])
        raise ErroUsuario("Não foi possível processar a mídia. O arquivo pode estar corrompido "
                          "ou a combinação de formatos não é suportada.")
    if saida and (not os.path.exists(saida) or os.path.getsize(saida) == 0):
        raise ErroUsuario("O FFmpeg não gerou um arquivo de saída. "
                          "Verifique se o arquivo tem o conteúdo necessário (ex.: uma faixa de áudio).")
