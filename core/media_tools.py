"""
media_tools.py — Ferramentas de mídia (áudio/vídeo)
Usa ffmpeg (do sistema ou via imageio-ffmpeg) para conversões de mídia.
"""

import os
import shutil
import subprocess
import logging

log = logging.getLogger(__name__)


def encontrar_ffmpeg():
    """Procura o ffmpeg no PATH do sistema ou via imageio-ffmpeg."""
    if shutil.which("ffmpeg"):
        return "ffmpeg"

    # 1. Tentar imageio_ffmpeg (pacote python com binário ffmpeg embutido)
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception as e:
        log.debug(f"imageio_ffmpeg não disponível: {e}")

    # 2. Caminhos comuns no Windows
    for c in [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
    ]:
        if os.path.exists(c):
            return c

    return None


def mp4_para_mp3(entrada: str, saida: str, bitrate: str = "192k", timeout: int = 180):
    """
    Converte um arquivo MP4 (vídeo) para MP3 (áudio).
    Extrai a faixa de áudio e recodifica em MP3.

    Args:
        entrada: Caminho do arquivo MP4 de entrada.
        saida: Caminho do arquivo MP3 de saída.
        bitrate: Bitrate do áudio (ex: "128k", "192k", "320k").
        timeout: Tempo máximo em segundos.
    """
    ffmpeg_exe = encontrar_ffmpeg()
    if not ffmpeg_exe:
        raise RuntimeError(
            "ffmpeg não foi encontrado. Certifique-se de ter o ffmpeg ou o pacote imageio-ffmpeg instalado."
        )

    if not os.path.exists(entrada):
        raise FileNotFoundError(f"Arquivo não encontrado: {entrada}")

    # Garantir que o diretório de saída existe
    os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)

    cmd = [
        ffmpeg_exe,
        "-i", os.path.abspath(entrada),
        "-vn",                 # Descartar fluxo de vídeo
        "-ar", "44100",        # Taxa de amostragem padrão
        "-ac", "2",            # Estéreo
        "-b:a", bitrate,       # Bitrate de áudio
        "-y",                  # Sobrescrever
        os.path.abspath(saida),
    ]

    log.info(f"Executando ffmpeg: {' '.join(cmd)}")

    resultado = subprocess.run(
        cmd,
        capture_output=True,
        timeout=timeout,
    )

    if resultado.returncode != 0:
        erro = resultado.stderr.decode("utf-8", errors="replace")
        log.warning(f"ffmpeg erro (código {resultado.returncode}): {erro}")
        raise RuntimeError("Erro ao extrair o áudio do vídeo. Verifique se o arquivo de vídeo não está corrompido.")

    if not os.path.exists(saida) or os.path.getsize(saida) == 0:
        raise RuntimeError("A conversão não gerou um arquivo de áudio válido.")

    log.info(f"MP4→MP3 OK: {os.path.basename(entrada)} ({bitrate})")


def _mp4_para_gif_opencv(entrada: str, saida: str, fps: int = 15, largura: int = 480):
    """Fallback usando OpenCV e Pillow se FFmpeg não estiver disponível."""
    try:
        import cv2
        from PIL import Image
    except ImportError as e:
        raise RuntimeError(f"Bibliotecas para conversão de mídia não disponíveis: {e}")

    cap = cv2.VideoCapture(entrada)
    if not cap.isOpened():
        raise RuntimeError("Não foi possível abrir o arquivo de vídeo MP4.")

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    passo = max(1, int(round(video_fps / fps)))

    frames = []
    idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % passo == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            if largura > 0 and img.width > largura:
                altura = int(img.height * (largura / img.width))
                img = img.resize((largura, altura), Image.Resampling.LANCZOS)
            frames.append(img)
        idx += 1

    cap.release()

    if not frames:
        raise RuntimeError("Nenhum frame extraído do vídeo MP4.")

    duracao_ms = int(1000 / fps)
    frames[0].save(
        saida,
        save_all=True,
        append_images=frames[1:],
        duration=duracao_ms,
        loop=0,
        optimize=True
    )


def mp4_para_gif(entrada: str, saida: str, fps: int = 15, largura: int = 480, timeout: int = 180):
    """
    Converte um arquivo MP4 (vídeo) para GIF animado.
    Tenta usar FFmpeg com palettegen/paletteuse para alta qualidade.
    Caso FFmpeg não esteja instalado, utiliza fallback com OpenCV + Pillow.

    Args:
        entrada: Caminho do arquivo MP4.
        saida: Caminho do arquivo GIF de saída.
        fps: Frames por segundo no GIF (10, 15, 20).
        largura: Largura máxima em pixels (320, 480, 640; 0 para original).
        timeout: Tempo limite em segundos.
    """
    if not os.path.exists(entrada):
        raise FileNotFoundError(f"Arquivo não encontrado: {entrada}")

    os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)

    ffmpeg_exe = encontrar_ffmpeg()

    if ffmpeg_exe:
        scale_filter = f"scale={largura}:-1:flags=lanczos," if largura > 0 else ""
        vf = f"fps={fps},{scale_filter}split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"

        cmd = [
            ffmpeg_exe,
            "-i", os.path.abspath(entrada),
            "-vf", vf,
            "-loop", "0",
            "-y",
            os.path.abspath(saida)
        ]

        log.info(f"Executando ffmpeg MP4->GIF: {' '.join(cmd)}")
        try:
            resultado = subprocess.run(cmd, capture_output=True, timeout=timeout)
            if resultado.returncode == 0 and os.path.exists(saida) and os.path.getsize(saida) > 0:
                log.info(f"MP4→GIF via FFmpeg OK: {os.path.basename(entrada)}")
                return
            log.warning("FFmpeg falhou ao gerar GIF. Tentando fallback com OpenCV...")
        except Exception as e:
            log.warning(f"Erro ao rodar FFmpeg ({e}). Tentando fallback com OpenCV...")

    # Fallback OpenCV
    _mp4_para_gif_opencv(entrada, saida, fps=fps, largura=largura)
    if not os.path.exists(saida) or os.path.getsize(saida) == 0:
        raise RuntimeError("A conversão para GIF não gerou um arquivo válido.")

    log.info(f"MP4→GIF via OpenCV OK: {os.path.basename(entrada)}")


def baixar_midia_url(url: str, pasta_destino: str, tipo: str = "mp4", progresso_callback=None) -> str:
    """
    Baixa vídeo ou áudio a partir de um link (YouTube, Instagram, Twitter/X, TikTok, etc.) usando yt-dlp.

    Args:
        url: Link do vídeo/post.
        pasta_destino: Diretório onde o arquivo será salvo.
        tipo: "mp4" para vídeo ou "mp3" para áudio.
        progresso_callback: Função callback(percent: float, status_msg: str) para progresso em tempo real.

    Returns:
        Caminho do arquivo final gerado.
    """
    try:
        import yt_dlp
    except ImportError:
        raise RuntimeError("A biblioteca yt-dlp não está instalada. Execute 'pip install yt-dlp'.")

    if not url or not url.strip():
        raise ValueError("URL inválida ou vazia.")

    os.makedirs(pasta_destino, exist_ok=True)
    out_pattern = os.path.join(pasta_destino, "%(title).100s_%(id)s.%(ext)s")

    def hook(d):
        if not progresso_callback:
            return
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            if total > 0:
                pct = round((downloaded / total) * 100, 1)
                progresso_callback(pct, f"Baixando... {pct}%")
            else:
                progresso_callback(50.0, "Baixando mídia...")
        elif status == "finished":
            progresso_callback(95.0, "Finalizando processamento do arquivo...")

    ffmpeg_exe = encontrar_ffmpeg()

    ydl_opts = {
        "outtmpl": out_pattern,
        "progress_hooks": [hook],
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "mweb", "web"],
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
        }
    }

    if ffmpeg_exe:
        # Se for caminho para o executável, passa o diretório ou o próprio caminho
        ydl_opts["ffmpeg_location"] = ffmpeg_exe

    # Suporte a cookies.txt para vídeos restritos se o arquivo existir na raiz do projeto
    for cookie_name in ["cookies.txt", "youtube_cookies.txt"]:
        if os.path.exists(cookie_name):
            ydl_opts["cookiefile"] = os.path.abspath(cookie_name)
            break

    if tipo == "mp3":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        ydl_opts.update({
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best",
            "merge_output_format": "mp4",
        })

    if progresso_callback:
        progresso_callback(5.0, "Obtendo informações do vídeo...")

    configs_tentativas = [
        # Estratégia 1: Cliente móvel mweb / android
        {"youtube": {"player_client": ["mweb", "android", "ios", "web"]}},
        # Estratégia 2: Cliente android exclusivo
        {"youtube": {"player_client": ["android", "ios"]}},
        # Estratégia 3: Padrão sem restrição de cliente
        {}
    ]

    ultimo_erro = None
    filename = None

    for idx, ext_args in enumerate(configs_tentativas):
        try:
            opts_atuais = ydl_opts.copy()
            if ext_args:
                opts_atuais["extractor_args"] = ext_args
            else:
                opts_atuais.pop("extractor_args", None)

            with yt_dlp.YoutubeDL(opts_atuais) as ydl:
                info = ydl.extract_info(url.strip(), download=True)
                cand = ydl.prepare_filename(info)

                if tipo == "mp3":
                    base_cand = os.path.splitext(cand)[0]
                    mp3_cand = base_cand + ".mp3"
                    if os.path.exists(mp3_cand):
                        cand = mp3_cand

                if cand and os.path.exists(cand) and os.path.getsize(cand) > 0:
                    filename = cand
                    break
        except Exception as e:
            ultimo_erro = e
            log.warning(f"Tentativa {idx + 1} com player_client {ext_args} falhou: {e}")

    if not filename or not os.path.exists(filename) or os.path.getsize(filename) == 0:
        # Procurar qualquer arquivo criado na pasta destino se o nome variou
        arquivos = [os.path.join(pasta_destino, f) for f in os.listdir(pasta_destino) if os.path.isfile(os.path.join(pasta_destino, f))]
        if arquivos:
            filename = sorted(arquivos, key=lambda p: os.path.getmtime(p), reverse=True)[0]
        elif ultimo_erro:
            raise ultimo_erro
        else:
            raise RuntimeError("Não foi possível gerar o arquivo de mídia baixado.")

    if progresso_callback:
        progresso_callback(100.0, "Download concluído!")

    return filename


