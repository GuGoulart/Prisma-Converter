"""video_downloader.py — Download de vídeo ou áudio por link, usando yt-dlp."""
import logging
import os

import yt_dlp

from core.errors import ErroUsuario, JobCancelado
from core.processo import Controle
from core.security import nome_seguro, validar_url_externa

log = logging.getLogger(__name__)

_QUALIDADES_VIDEO = {
    "1080p": "bv*[height<=1080]+ba/b[height<=1080]/best[height<=1080]/best",
    "720p": "bv*[height<=720]+ba/b[height<=720]/best[height<=720]/best",
    "480p": "bv*[height<=480]+ba/b[height<=480]/best[height<=480]/best",
}


def baixar_video_por_link(url: str, pasta: str, formato: str = "mp4", qualidade: str = "best",
                          controle: Controle | None = None) -> tuple[str, str]:
    """Baixa em `pasta` e retorna (caminho do arquivo, nome sugerido para download)."""
    url = validar_url_externa(url)
    controle = controle or Controle()
    formato = formato if formato in ("mp4", "mp3") else "mp4"

    def _progresso(d: dict):
        if controle.cancelado:
            raise yt_dlp.utils.DownloadCancelled()
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total:
                controle.ao_progredir(d.get("downloaded_bytes", 0) / total * 95)

    opcoes = {
        "outtmpl": os.path.join(pasta, "media.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "progress_hooks": [_progresso],
        "socket_timeout": 30,
        "retries": 5,
        "fragment_retries": 5,
    }
    if formato == "mp3":
        kbps = str(qualidade).lower().replace("k", "")
        opcoes.update({
            "format": "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
                                "preferredquality": kbps if kbps in ("128", "192", "256", "320") else "320"}],
        })
    else:
        opcoes.update({"format": _QUALIDADES_VIDEO.get(qualidade, "bv*+ba/b/best"), "merge_output_format": "mp4"})

    try:
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            info = ydl.extract_info(url, download=True)
    except yt_dlp.utils.DownloadCancelled:
        raise JobCancelado() from None
    except yt_dlp.utils.DownloadError as e:
        log.error("Falha no yt-dlp: %s", e)
        if "Unsupported URL" in str(e):
            raise ErroUsuario("Este link não é suportado ou é privado.") from None
        raise ErroUsuario("Não foi possível baixar o vídeo. Verifique o link e tente novamente.") from None

    arquivos = [os.path.join(pasta, n) for n in os.listdir(pasta) if n.startswith("media.")]
    if not arquivos:
        raise ErroUsuario("O download terminou, mas o arquivo não foi gerado.")
    caminho = max(arquivos, key=os.path.getsize)
    ext = os.path.splitext(caminho)[1]
    return caminho, nome_seguro(f"{info.get('title') or 'video'}{ext}", "video")
