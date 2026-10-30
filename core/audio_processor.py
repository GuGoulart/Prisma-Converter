"""audio_processor.py — Processamento de áudio via FFmpeg e transcrição local com Whisper."""
import json
import logging
import os
import re

from core.errors import ErroUsuario
from core.ffmpeg import obter_duracao, rodar_ffmpeg
from core.processo import Controle, executar
from core.progresso import avisar, reportar

log = logging.getLogger(__name__)

FORMATOS_SUPORTADOS = ["mp3", "wav", "aac", "ogg", "flac", "m4a", "opus"]
BITRATES_SUPORTADOS = ["64k", "96k", "128k", "192k", "256k", "320k"]
AJUSTES_VOLUME = {"+3", "+6", "+12", "+18", "-3", "-6", "-12", "normalizar"}
VELOCIDADE_MIN = 0.5
VELOCIDADE_MAX = 2.0
MODELOS_WHISPER = ["base", "small", "medium", "large-v3", "turbo"]

_CODECS = {
    "mp3": "libmp3lame", "wav": "pcm_s16le", "aac": "aac", "ogg": "libvorbis",
    "flac": "flac", "m4a": "aac", "m4b": "aac", "opus": "libopus",
}
_SEM_PERDA = {"wav", "flac", "aiff", "aif"}


def _args_codec(ext: str, bitrate: str = "192k") -> list[str]:
    """Codec para a extensão de saída. Formatos sem mapeamento ficam com o padrão do FFmpeg."""
    args = ["-codec:a", _CODECS[ext]] if ext in _CODECS else []
    if ext not in _SEM_PERDA:
        args += ["-b:a", bitrate]
    return args


def _ext(caminho: str) -> str:
    return os.path.splitext(caminho)[1].lstrip(".").lower()


def converter_audio(entrada: str, saida: str, formato: str, bitrate: str = "192k", canais: int = 2,
                    sample_rate: int = 44100, controle: Controle | None = None) -> None:
    if formato not in FORMATOS_SUPORTADOS:
        raise ErroUsuario(f"Formato '{formato}' não suportado.")
    # O libopus não aceita 44,1 kHz.
    taxa = 48000 if formato == "opus" else sample_rate
    args = ["-i", entrada, "-vn", "-ac", str(canais), "-ar", str(taxa), *_args_codec(formato, bitrate), saida]
    rodar_ffmpeg(args, controle, obter_duracao(entrada), saida=saida)


def parse_tempo(texto: str) -> float:
    """Converte "90", "1:30" ou "0:10:30" em segundos."""
    try:
        partes = [float(p) for p in texto.strip().split(":")]
        if not 1 <= len(partes) <= 3 or any(p < 0 for p in partes):
            raise ValueError
    except ValueError:
        raise ErroUsuario(f"Tempo inválido: '{texto}'. Use MM:SS ou HH:MM:SS.") from None
    segundos = 0.0
    for parte in partes:
        segundos = segundos * 60 + parte
    return segundos


def cortar_audio(entrada: str, saida: str, inicio: float, fim: float | None = None,
                 controle: Controle | None = None) -> None:
    """Corta entre `inicio` e `fim` (até o final do arquivo, se `fim` for None)."""
    inicio = max(0.0, inicio)
    if fim is not None and fim <= inicio:
        raise ErroUsuario("O tempo final deve ser maior que o tempo inicial.")
    total = obter_duracao(entrada)
    if total and inicio >= total:
        raise ErroUsuario("O tempo inicial está depois do fim do áudio.")
    trecho = ["-t", str(fim - inicio)] if fim is not None else []
    duracao = (fim if fim is not None else total) - inicio if total else 0.0
    base = ["-ss", str(inicio), "-i", entrada, *trecho, "-vn"]
    try:
        rodar_ffmpeg([*base, "-acodec", "copy", saida], controle, duracao, saida=saida)
    except ErroUsuario:
        rodar_ffmpeg([*base, *_args_codec(_ext(saida)), saida], controle, duracao, saida=saida)


def juntar_audios(entradas: list[str], saida: str, formato: str = "mp3", bitrate: str = "192k",
                  controle: Controle | None = None) -> None:
    if len(entradas) < 2:
        raise ErroUsuario("São necessários pelo menos 2 arquivos para juntar.")
    # O filtro concat reencoda, então aceita faixas com formatos e taxas diferentes.
    args: list[str] = []
    for caminho in entradas:
        args += ["-i", caminho]
    rotulos = "".join(f"[{i}:a:0]" for i in range(len(entradas)))
    args += ["-filter_complex", f"{rotulos}concat=n={len(entradas)}:v=0:a=1[a]", "-map", "[a]",
             *_args_codec(formato, bitrate), saida]
    rodar_ffmpeg(args, controle, sum(obter_duracao(c) for c in entradas), saida=saida)


def ajustar_volume(entrada: str, saida: str, ajuste: str = "+6", controle: Controle | None = None) -> None:
    if ajuste not in AJUSTES_VOLUME:
        raise ErroUsuario("Ajuste de volume inválido.")
    duracao = obter_duracao(entrada)
    if ajuste == "normalizar":
        filtro = _filtro_loudnorm(entrada, controle)
    else:
        filtro = f"volume={float(ajuste)}dB"
    rodar_ffmpeg(["-i", entrada, "-af", filtro, "-vn", *_args_codec(_ext(saida)), saida],
                 controle, duracao, saida=saida)


def _filtro_loudnorm(entrada: str, controle: Controle | None) -> str:
    """Primeira passada da normalização EBU R128: mede o áudio para a segunda ser precisa."""
    padrao = "loudnorm=I=-16:TP=-1.5:LRA=11"
    r = executar(["ffmpeg", "-y", "-nostdin", "-hide_banner", "-i", entrada,
                  "-af", padrao + ":print_format=json", "-f", "null", "-"], controle, timeout=1800)
    m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr, re.DOTALL)
    if not m:
        return padrao
    try:
        d = json.loads(m.group())
        return (f"{padrao}:measured_I={d['input_i']}:measured_TP={d['input_tp']}:"
                f"measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:"
                f"offset={d['target_offset']}:linear=true")
    except (ValueError, KeyError):
        return padrao


def alterar_velocidade(entrada: str, saida: str, fator: float = 1.5, controle: Controle | None = None) -> None:
    """Altera a velocidade sem alterar o tom. O filtro atempo aceita de 0.5 a 2.0."""
    if not VELOCIDADE_MIN <= fator <= VELOCIDADE_MAX:
        raise ErroUsuario(f"O fator deve estar entre {VELOCIDADE_MIN}x e {VELOCIDADE_MAX}x.")
    duracao = obter_duracao(entrada) / fator
    rodar_ffmpeg(["-i", entrada, "-af", f"atempo={fator:.4f}", "-vn", *_args_codec(_ext(saida)), saida],
                 controle, duracao, saida=saida)


def inverter_audio(entrada: str, saida: str, controle: Controle | None = None) -> None:
    rodar_ffmpeg(["-i", entrada, "-af", "areverse", "-vn", *_args_codec(_ext(saida)), saida],
                 controle, obter_duracao(entrada), saida=saida)


# ── Transcrição ───────────────────────────────────────────────
def _tempo_srt(segundos: float) -> str:
    total = int(segundos)
    return f"{total // 3600:02d}:{total % 3600 // 60:02d}:{total % 60:02d},{int((segundos - total) * 1000):03d}"


def _formatar_duracao(segundos: float) -> str:
    s = int(segundos)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60:02d}:{s % 60:02d}"


def transcrever_audio(entrada: str, saida: str, idioma: str = "auto", formato: str = "txt",
                      modelo: str = "small") -> dict:
    """Transcreve 100% localmente. Na primeira vez o modelo escolhido é baixado (uma única vez)."""
    from faster_whisper import WhisperModel

    if modelo not in MODELOS_WHISPER:
        modelo = "small"
    wav = entrada + ".16k.wav"
    rodar_ffmpeg(["-i", entrada, "-ar", "16000", "-ac", "1", "-codec:a", "pcm_s16le", "-vn", wav], saida=wav)
    try:
        reportar(5)
        whisper = WhisperModel(modelo, device="cpu", compute_type="int8")
        reportar(10)
        segmentos, info = whisper.transcribe(
            wav, language=None if idioma == "auto" else idioma, beam_size=5,
            vad_filter=True, vad_parameters={"min_silence_duration_ms": 500},
        )
        duracao = info.duration or 0.0
        partes = []
        for seg in segmentos:
            texto = seg.text.strip()
            if texto:
                partes.append({"inicio": round(seg.start, 2), "fim": round(seg.end, 2), "texto": texto})
            if duracao:
                reportar(10 + min(seg.end / duracao, 1.0) * 89)
    finally:
        if os.path.exists(wav):
            os.remove(wav)

    texto = " ".join(p["texto"] for p in partes)
    if not texto:
        avisar("Nenhuma fala foi detectada no arquivo.")
    if formato == "srt":
        conteudo = "\n".join(f"{i}\n{_tempo_srt(p['inicio'])} --> {_tempo_srt(p['fim'])}\n{p['texto']}\n"
                             for i, p in enumerate(partes, 1))
    elif formato == "json":
        conteudo = json.dumps({"transcricao": texto, "idioma": info.language, "duracao_segundos": round(duracao, 2),
                               "segmentos": partes}, ensure_ascii=False, indent=2)
    else:
        conteudo = f"Idioma: {info.language} | Duração: {_formatar_duracao(duracao)}\n\n{texto}\n"
    with open(saida, "w", encoding="utf-8") as f:
        f.write(conteudo)
    return {"texto": texto}
