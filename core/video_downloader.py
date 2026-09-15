"""
core/video_downloader.py — Módulo para baixar vídeos via URL (YouTube, Twitter, Instagram, TikTok, etc.)
usando a biblioteca yt-dlp.
"""
import os
import re
import uuid
import time
import threading
import logging
import yt_dlp
from werkzeug.utils import secure_filename

from core.utils import caminho_download, formatar_tamanho


log = logging.getLogger(__name__)

_PROGRESS_STORE = {}
_PROGRESS_LOCK = threading.Lock()


def obter_progresso_download(task_id: str) -> dict:
    """Retorna o progresso em tempo real (porcentagem, velocidade, ETA) de um download."""
    if not task_id:
        return {'status': 'idle', 'pct': 0.0, 'pct_str': '0%', 'speed': '', 'eta': ''}
    with _PROGRESS_LOCK:
        return _PROGRESS_STORE.get(task_id, {
            'status': 'starting',
            'pct': 0.0,
            'pct_str': '0%',
            'speed': '',
            'eta': ''
        })


def _limpar_progresso_antigo():
    now = time.time()
    with _PROGRESS_LOCK:
        keys_to_del = [k for k, v in _PROGRESS_STORE.items() if now - v.get('time', now) > 600]
        for k in keys_to_del:
            del _PROGRESS_STORE[k]


def baixar_video_por_link(
    url: str,
    formato_saida: str = "mp4",
    qualidade: str = "best",
    task_id: str = None
) -> tuple[bool, str, str, str]:
    """
    Baixa vídeo ou áudio de um link fornecido (YouTube, Twitter/X, Instagram, etc.)
    e transmite progresso em tempo real via task_id.
    Retorna (sucesso, mensagem_erro, caminho_saida, nome_original_ou_titulo).
    """
    if not url or not url.startswith(("http://", "https://")):
        return False, "Informe uma URL válida (ex: https://youtube.com/watch?...)", "", ""

    _limpar_progresso_antigo()

    formato_saida = formato_saida.lower().strip()
    if formato_saida not in ["mp4", "mp3"]:
        formato_saida = "mp4"

    id_unico = uuid.uuid4().hex
    template_saida = os.path.join("downloads", f"{id_unico}_%(title)s.%(ext)s")

    def progress_hook(d):
        if not task_id:
            return
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            pct = (downloaded / total * 100) if total > 0 else 0.0
            
            raw_pct_str = d.get('_percent_str', f'{pct:.1f}%').strip()
            pct_str = re.sub(r'\x1b\[[0-9;]*m', '', raw_pct_str)
            
            raw_speed = d.get('_speed_str', '').strip()
            speed = re.sub(r'\x1b\[[0-9;]*m', '', raw_speed)
            
            raw_eta = d.get('_eta_str', '').strip()
            eta = re.sub(r'\x1b\[[0-9;]*m', '', raw_eta)

            with _PROGRESS_LOCK:
                _PROGRESS_STORE[task_id] = {
                    'status': 'downloading',
                    'pct': round(pct, 1),
                    'pct_str': pct_str,
                    'speed': speed,
                    'eta': eta,
                    'time': time.time()
                }
        elif d['status'] == 'finished':
            with _PROGRESS_LOCK:
                _PROGRESS_STORE[task_id] = {
                    'status': 'finished',
                    'pct': 100.0,
                    'pct_str': '100%',
                    'speed': '',
                    'eta': '',
                    'time': time.time()
                }

    ydl_opts = {
        'outtmpl': template_saida,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'overwrites': True,
        'progress_hooks': [progress_hook],
        'nocheckcertificate': True,
        'socket_timeout': 30,
        'retries': 10,
        'fragment_retries': 10,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web', 'mweb'],
            }
        }
    }

    if formato_saida == "mp3":
        qualidade_limpa = str(qualidade or "320").lower().replace("k", "").strip()
        if qualidade_limpa in ["320", "max", "best"]:
            bitrate_mp3 = "320"
        elif qualidade_limpa in ["256"]:
            bitrate_mp3 = "256"
        elif qualidade_limpa in ["128"]:
            bitrate_mp3 = "128"
        elif qualidade_limpa in ["192"]:
            bitrate_mp3 = "192"
        else:
            bitrate_mp3 = "320"

        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': bitrate_mp3,
            }],
        })
    else:
        if qualidade == "1080p":
            format_spec = 'bv*[height<=1080]+ba/b[height<=1080]/best[height<=1080]/best'
        elif qualidade == "720p":
            format_spec = 'bv*[height<=720]+ba/b[height<=720]/best[height<=720]/best'
        elif qualidade == "480p":
            format_spec = 'bv*[height<=480]+ba/b[height<=480]/best[height<=480]/best'
        else:
            format_spec = 'bv*+ba/b/best'

        ydl_opts.update({
            'format': format_spec,
            'merge_output_format': 'mp4',
        })

    try:
        log.info(f"[video_downloader] Baixando URL: {url} ({formato_saida}) - Task: {task_id}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            titulo = info.get('title', 'video_baixado')
            
            arquivo_gerado = None
            for nome_arq in os.listdir("downloads"):
                if nome_arq.startswith(id_unico):
                    caminho_bruto = os.path.join("downloads", nome_arq)
                    ext = nome_arq.rsplit('.', 1)[-1].lower() if '.' in nome_arq else formato_saida
                    nome_limpo_base = secure_filename(titulo) or "media_baixada"
                    novo_nome = f"{id_unico}_{nome_limpo_base}.{ext}"
                    novo_caminho = os.path.join("downloads", novo_nome)
                    try:
                        if caminho_bruto != novo_caminho:
                            if os.path.exists(novo_caminho):
                                os.remove(novo_caminho)
                            os.rename(caminho_bruto, novo_caminho)
                            arquivo_gerado = novo_caminho
                        else:
                            arquivo_gerado = caminho_bruto
                    except Exception as e:
                        log.warning(f"[video_downloader] Falha ao renomear {caminho_bruto}: {e}")
                        arquivo_gerado = caminho_bruto
                    break

            if arquivo_gerado and os.path.exists(arquivo_gerado) and os.path.getsize(arquivo_gerado) > 0:
                log.info(f"[video_downloader] Download concluído: {arquivo_gerado}")
                return True, "", arquivo_gerado, titulo
            else:
                return False, "O arquivo baixado não pôde ser encontrado no servidor.", "", ""

    except yt_dlp.utils.DownloadError as de:
        log.error(f"[video_downloader] Erro no download: {de}")
        msg = str(de)
        if "Unsupported URL" in msg:
            return False, "URL não suportada ou privada. Verifique o link enviado.", "", ""
        return False, f"Erro ao baixar o vídeo: {msg.split(';')[-1]}", "", ""
    except Exception as e:
        log.exception("[video_downloader] Exceção inesperada no download")
        return False, f"Erro no processamento da URL: {str(e)}", "", ""
