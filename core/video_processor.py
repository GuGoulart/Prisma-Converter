"""video_processor.py — Processamento de vídeo via FFmpeg."""
from core.errors import ErroUsuario
from core.ffmpeg import obter_duracao, rodar_ffmpeg
from core.processo import Controle

FORMATOS_SAIDA = ["mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "m4v"]
BITRATES_MP3 = ["128k", "192k", "256k", "320k"]
NIVEIS_COMPRESSAO = {
    "whatsapp": ["-vf", "scale='min(720,iw)':-2", "-c:v", "libx264", "-crf", "28", "-preset", "faster",
                 "-c:a", "aac", "-b:a", "96k"],
    "medio": ["-c:v", "libx264", "-crf", "26", "-preset", "faster", "-c:a", "aac", "-b:a", "128k"],
    "leve": ["-c:v", "libx264", "-crf", "23", "-preset", "fast", "-c:a", "aac", "-b:a", "160k"],
}
_CODECS_FORMATO = {
    "webm": ["-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0", "-c:a", "libopus"],
    "avi": ["-c:v", "mpeg4", "-vtag", "xvid", "-q:v", "4", "-c:a", "libmp3lame"],
    "wmv": ["-c:v", "wmv2", "-q:v", "4", "-c:a", "wmav2"],
}
_CODECS_PADRAO = ["-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "aac"]


def converter_mp4_para_mp3(entrada: str, saida: str, bitrate: str = "192k", controle: Controle | None = None) -> None:
    rodar_ffmpeg(["-i", entrada, "-vn", "-acodec", "libmp3lame", "-b:a", bitrate, saida],
                 controle, obter_duracao(entrada), saida=saida)


def converter_mp4_para_gif(entrada: str, saida: str, inicio: float = 0.0, duracao: float = 5.0, fps: int = 10,
                           largura: int = 480, controle: Controle | None = None) -> None:
    filtro = (f"[0:v]fps={max(1, min(fps, 30))},scale={max(160, min(largura, 1080))}:-1:flags=lanczos,"
              "split[s0][s1];[s0]palettegen=stats_mode=full[p];[s1][p]paletteuse=dither=sierra2_4a")
    args = ["-ss", str(max(0.0, inicio))]
    if duracao > 0:
        args += ["-t", str(duracao)]
    rodar_ffmpeg([*args, "-i", entrada, "-filter_complex", filtro, saida], controle, duracao, saida=saida)


def converter_formato_video(entrada: str, saida: str, formato: str = "mp4", controle: Controle | None = None) -> None:
    if formato not in FORMATOS_SAIDA:
        raise ErroUsuario(f"Formato de vídeo '{formato}' não suportado.")
    rodar_ffmpeg(["-i", entrada, *_CODECS_FORMATO.get(formato, _CODECS_PADRAO), saida],
                 controle, obter_duracao(entrada), saida=saida)


def compressor_video(entrada: str, saida: str, nivel: str = "medio", controle: Controle | None = None) -> None:
    args = NIVEIS_COMPRESSAO.get(nivel, NIVEIS_COMPRESSAO["medio"])
    rodar_ffmpeg(["-i", entrada, *args, saida], controle, obter_duracao(entrada), saida=saida)


def remover_audio_video(entrada: str, saida: str, controle: Controle | None = None) -> None:
    rodar_ffmpeg(["-i", entrada, "-an", "-c:v", "copy", saida], controle, obter_duracao(entrada), saida=saida)


def capturar_foto_video(entrada: str, saida: str, tempo: float = 1.0, controle: Controle | None = None) -> None:
    total = obter_duracao(entrada)
    if total and tempo >= total:
        raise ErroUsuario(f"O vídeo tem apenas {total:.1f} segundos. Escolha um tempo menor.")
    rodar_ffmpeg(["-ss", str(max(0.0, tempo)), "-i", entrada, "-frames:v", "1", "-q:v", "2", "-update", "1", saida],
                 controle, saida=saida)
