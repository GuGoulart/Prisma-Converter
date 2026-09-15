"""
core/video_processor.py — Módulo de processamento de vídeo (MP4 para MP3, MP4 para GIF).

Funções:
  - converter_mp4_para_mp3(): Extrai áudio de arquivo de vídeo para MP3.
  - converter_mp4_para_gif(): Converte trecho de vídeo para GIF animado de alta qualidade.
  - obter_duracao_video(): Retorna duração em segundos do vídeo.
"""
import os
import re
import subprocess
import logging

log = logging.getLogger(__name__)

FORMATOS_VIDEO_SUPORTADOS = ["mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "m4v", "3gp"]
BITRATES_MP3 = ["128k", "192k", "256k", "320k"]


def obter_duracao_video(caminho: str) -> float:
    """Retorna a duração do vídeo em segundos usando ffprobe ou ffmpeg."""
    # 1. Tentar com ffprobe
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            caminho
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and res.stdout.strip():
            return float(res.stdout.strip())
    except Exception as e:
        log.debug(f"[ffprobe] Fallback para ffmpeg parser: {e}")

    # 2. Fallback com ffmpeg -i
    try:
        cmd = ["ffmpeg", "-i", caminho]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception as e:
        log.error(f"[video_duration] Erro ao obter duração: {e}")

    return 0.0


def converter_mp4_para_mp3(caminho_in: str, caminho_out: str, bitrate: str = "192k") -> tuple[bool, str]:
    """
    Extrai a faixa de áudio de um vídeo e salva em formato MP3.
    """
    if bitrate not in BITRATES_MP3:
        bitrate = "192k"

    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", caminho_in,
            "-vn",
            "-acodec", "libmp3lame",
            "-b:a", bitrate,
            caminho_out
        ]
        log.info(f"[mp4_to_mp3] Executando: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if res.returncode == 0 and os.path.exists(caminho_out) and os.path.getsize(caminho_out) > 0:
            return True, ""
        
        err_msg = res.stderr or "Falha na conversão de MP4 para MP3."
        log.error(f"[mp4_to_mp3] Erro: {err_msg}")
        return False, err_msg
    except Exception as e:
        log.exception("[mp4_to_mp3] Exceção ao converter MP4 para MP3")
        return False, str(e)


def converter_mp4_para_gif(
    caminho_in: str,
    caminho_out: str,
    inicio: float = 0.0,
    duracao: float = None,
    fps: int = 10,
    largura: int = 480
) -> tuple[bool, str]:
    """
    Converte um vídeo (ou trecho dele) em GIF animado de alta qualidade
    utilizando a técnica de geração de paleta do FFmpeg.
    """
    try:
        fps = max(1, min(fps, 30))
        largura = max(160, min(largura, 1080))

        ss_args = []
        if inicio > 0:
            ss_args.extend(["-ss", str(inicio)])
        if duracao is not None and duracao > 0:
            ss_args.extend(["-t", str(duracao)])

        # Filtro de paleta do FFmpeg para evitar banding/dithering feio
        filter_str = f"[0:v]fps={fps},scale={largura}:-1:flags=lanczos,split[s0][s1];[s0]palettegen=stats_mode=full[p];[s1][p]paletteuse=dither=sierra2_4a"

        cmd = [
            "ffmpeg", "-y",
            *ss_args,
            "-i", caminho_in,
            "-filter_complex", filter_str,
            caminho_out
        ]

        log.info(f"[mp4_to_gif] Executando: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if res.returncode == 0 and os.path.exists(caminho_out) and os.path.getsize(caminho_out) > 0:
            return True, ""

        err_msg = res.stderr or "Falha na conversão de MP4 para GIF."
        log.error(f"[mp4_to_gif] Erro: {err_msg}")
        return False, err_msg
    except Exception as e:
        log.exception("[mp4_to_gif] Exceção ao converter MP4 para GIF")
        return False, str(e)


def converter_formato_video(caminho_in: str, caminho_out: str, formato_saida: str = "mp4") -> tuple[bool, str]:
    """Converte um vídeo para outro formato (mp4, webm, mov, avi, mkv)."""
    formato_saida = formato_saida.lower().strip()
    if formato_saida not in FORMATOS_VIDEO_SUPORTADOS:
        formato_saida = "mp4"

    if formato_saida == "webm":
        codec_args = ["-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0", "-c:a", "libopus"]
    elif formato_saida == "avi":
        codec_args = ["-c:v", "mpeg4", "-vtag", "xvid", "-q:v", "4", "-c:a", "mp3"]
    else:
        codec_args = ["-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "aac"]

    try:
        cmd = ["ffmpeg", "-y", "-i", caminho_in, *codec_args, caminho_out]
        log.info(f"[converter_formato_video] Executando: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if res.returncode == 0 and os.path.exists(caminho_out) and os.path.getsize(caminho_out) > 0:
            return True, ""
        return False, res.stderr or "Falha ao converter formato do vídeo."
    except Exception as e:
        log.exception("[converter_formato_video] Exceção na conversão")
        return False, str(e)


def compressor_video(caminho_in: str, caminho_out: str, nivel: str = "medio") -> tuple[bool, str]:
    """Reduz o tamanho do vídeo (whatsapp: ~70%, medio: ~50%, leve: ~30%)."""
    nivel = nivel.lower().strip()
    if nivel == "whatsapp":
        args = ["-vf", "scale='min(720,iw)':-2", "-c:v", "libx264", "-crf", "28", "-preset", "faster", "-c:a", "aac", "-b:a", "96k"]
    elif nivel == "medio":
        args = ["-c:v", "libx264", "-crf", "26", "-preset", "faster", "-c:a", "aac", "-b:a", "128k"]
    else:
        args = ["-c:v", "libx264", "-crf", "23", "-preset", "fast", "-c:a", "aac", "-b:a", "160k"]

    try:
        cmd = ["ffmpeg", "-y", "-i", caminho_in, *args, caminho_out]
        log.info(f"[compressor_video] Executando ({nivel}): {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if res.returncode == 0 and os.path.exists(caminho_out) and os.path.getsize(caminho_out) > 0:
            return True, ""
        return False, res.stderr or "Falha ao comprimir vídeo."
    except Exception as e:
        log.exception("[compressor_video] Exceção ao comprimir vídeo")
        return False, str(e)


def remover_audio_video(caminho_in: str, caminho_out: str) -> tuple[bool, str]:
    """Remove a faixa de áudio do vídeo sem re-codificação (-an -c:v copy)."""
    try:
        cmd = ["ffmpeg", "-y", "-i", caminho_in, "-an", "-c:v", "copy", caminho_out]
        log.info(f"[remover_audio_video] Executando: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if res.returncode == 0 and os.path.exists(caminho_out) and os.path.getsize(caminho_out) > 0:
            return True, ""
        return False, res.stderr or "Falha ao remover áudio do vídeo."
    except Exception as e:
        log.exception("[remover_audio_video] Exceção ao remover áudio")
        return False, str(e)


def capturar_foto_video(caminho_in: str, caminho_out: str, tempo: float = 1.0) -> tuple[bool, str]:
    """Extrai uma imagem (frame HD) do vídeo em um segundo específico."""
    try:
        if tempo < 0:
            tempo = 0.0

        cmd = ["ffmpeg", "-y", "-ss", str(tempo), "-i", caminho_in, "-vframes", "1", "-q:v", "2", caminho_out]
        log.info(f"[capturar_foto_video] Executando ({tempo}s): {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if res.returncode == 0 and os.path.exists(caminho_out) and os.path.getsize(caminho_out) > 0:
            return True, ""
        return False, res.stderr or "Falha ao capturar imagem do vídeo."
    except Exception as e:
        log.exception("[capturar_foto_video] Exceção ao capturar imagem")
        return False, str(e)

