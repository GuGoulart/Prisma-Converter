"""
audio_processor.py — Motor de processamento de áudio para o Prisma Audio.

Usa pydub (wrapper FFmpeg) e chamadas diretas ao FFmpeg via subprocess
para operações que exigem filtros avançados (atempo, areverse).

Requisito: FFmpeg instalado e disponível no PATH do sistema.
"""
import os
import subprocess
import logging
import shutil
from typing import List

log = logging.getLogger(__name__)


def _ffmpeg_disponivel() -> bool:
    """Verifica se o FFmpeg está disponível no PATH."""
    return shutil.which("ffmpeg") is not None


def _run_ffmpeg(args: list, timeout: int = 300) -> tuple[bool, str]:
    """
    Executa um comando ffmpeg e retorna (sucesso, mensagem_erro).
    """
    cmd = ["ffmpeg", "-y"] + args
    log.info(f"[ffmpeg] Executando: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0:
            log.error(f"[ffmpeg] Erro (código {result.returncode}): {result.stderr[-500:]}")
            return False, result.stderr[-300:] or "Erro desconhecido no FFmpeg."
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "Tempo limite excedido ao processar o áudio."
    except FileNotFoundError:
        return False, "FFmpeg não encontrado. Instale o FFmpeg e adicione ao PATH."
    except Exception as e:
        log.exception("[ffmpeg] Exceção inesperada")
        return False, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# 1. CONVERSOR UNIVERSAL
# ─────────────────────────────────────────────────────────────────────────────

FORMATOS_SUPORTADOS = ["mp3", "wav", "aac", "ogg", "flac", "m4a", "opus"]
BITRATES_SUPORTADOS = ["64k", "96k", "128k", "192k", "256k", "320k"]

# Mapeamento de codec para cada formato de saída
_CODEC_MAP = {
    "mp3": "libmp3lame",
    "wav": "pcm_s16le",
    "aac": "aac",
    "ogg": "libvorbis",
    "flac": "flac",
    "m4a": "aac",
    "opus": "libopus",
}

# Mapeamento de container de saída
_CONTAINER_MAP = {
    "mp3": "mp3",
    "wav": "wav",
    "aac": "adts",
    "ogg": "ogg",
    "flac": "flac",
    "m4a": "mp4",
    "opus": "ogg",
}


def converter_audio(
    caminho_entrada: str,
    caminho_saida: str,
    formato_saida: str,
    bitrate: str = "192k"
) -> tuple[bool, str]:
    """
    Converte áudio para o formato especificado com a taxa de bits desejada.

    Args:
        caminho_entrada: Caminho do arquivo de áudio de entrada.
        caminho_saida: Caminho do arquivo de saída.
        formato_saida: Formato destino (mp3, wav, aac, ogg, flac, m4a, opus).
        bitrate: Taxa de bits (128k, 192k, 320k).

    Returns:
        (True, "") em sucesso, ou (False, mensagem_erro).
    """
    if formato_saida not in FORMATOS_SUPORTADOS:
        return False, f"Formato '{formato_saida}' não suportado. Use: {', '.join(FORMATOS_SUPORTADOS)}"

    if bitrate not in BITRATES_SUPORTADOS:
        bitrate = "192k"

    codec = _CODEC_MAP[formato_saida]
    args = ["-i", caminho_entrada]

    # Codec e bitrate
    args += ["-codec:a", codec]

    # Formatos sem bitrate variável (WAV e FLAC são lossless)
    if formato_saida not in ("wav", "flac"):
        if formato_saida == "opus":
            args += ["-b:a", bitrate]
        else:
            args += ["-b:a", bitrate]

    # Sem vídeo
    args += ["-vn", caminho_saida]

    return _run_ffmpeg(args)


# ─────────────────────────────────────────────────────────────────────────────
# 2. AUDIO CUTTER
# ─────────────────────────────────────────────────────────────────────────────

def cortar_audio(
    caminho_entrada: str,
    caminho_saida: str,
    inicio: float,
    fim: float
) -> tuple[bool, str]:
    """
    Corta um trecho do áudio entre inicio e fim (em segundos).

    Args:
        caminho_entrada: Arquivo de entrada.
        caminho_saida: Arquivo de saída.
        inicio: Tempo inicial em segundos (ex: 10.5).
        fim: Tempo final em segundos (ex: 90.0).

    Returns:
        (True, "") em sucesso, ou (False, mensagem_erro).
    """
    if inicio < 0:
        inicio = 0.0
    if fim <= inicio:
        return False, "O tempo final deve ser maior que o tempo inicial."

    duracao = fim - inicio
    args = [
        "-i", caminho_entrada,
        "-ss", str(inicio),
        "-t", str(duracao),
        "-acodec", "copy",
        "-vn",
        caminho_saida
    ]

    ok, err = _run_ffmpeg(args)
    if not ok:
        # Tenta com recodificação se copy falhar
        args_recodifica = [
            "-i", caminho_entrada,
            "-ss", str(inicio),
            "-t", str(duracao),
            "-vn",
            caminho_saida
        ]
        ok, err = _run_ffmpeg(args_recodifica)

    return ok, err


def parse_tempo(tempo_str: str) -> float:
    """
    Converte string de tempo para segundos.
    Formatos aceitos: "1:30", "0:10:30", "90", "90.5"
    """
    tempo_str = tempo_str.strip()
    try:
        partes = tempo_str.split(":")
        if len(partes) == 1:
            return float(partes[0])
        elif len(partes) == 2:
            return int(partes[0]) * 60 + float(partes[1])
        elif len(partes) == 3:
            return int(partes[0]) * 3600 + int(partes[1]) * 60 + float(partes[2])
        else:
            raise ValueError("Formato inválido")
    except Exception:
        raise ValueError(f"Tempo inválido: '{tempo_str}'. Use formato MM:SS ou HH:MM:SS")


# ─────────────────────────────────────────────────────────────────────────────
# 3. AUDIO JOINER / MERGER
# ─────────────────────────────────────────────────────────────────────────────

def juntar_audios(
    caminhos_entrada: List[str],
    caminho_saida: str,
    formato_saida: str = "mp3",
    bitrate: str = "192k"
) -> tuple[bool, str]:
    """
    Concatena múltiplos arquivos de áudio em sequência.

    Args:
        caminhos_entrada: Lista de arquivos a concatenar (na ordem dada).
        caminho_saida: Arquivo de saída.
        formato_saida: Formato de saída (padrão: mp3).
        bitrate: Taxa de bits (padrão: 192k).

    Returns:
        (True, "") em sucesso, ou (False, mensagem_erro).
    """
    if len(caminhos_entrada) < 2:
        return False, "São necessários pelo menos 2 arquivos para juntar."

    # Cria arquivo de lista temporário para o filter_complex concat
    lista_path = caminho_saida + ".list.txt"
    try:
        with open(lista_path, "w", encoding="utf-8") as f:
            for caminho in caminhos_entrada:
                # Escapa aspas simples no caminho
                caminho_seguro = os.path.abspath(caminho).replace("'", "'\\''")
                f.write(f"file '{caminho_seguro}'\n")

        args = [
            "-f", "concat",
            "-safe", "0",
            "-i", lista_path,
            "-vn",
        ]

        codec = _CODEC_MAP.get(formato_saida, "libmp3lame")
        args += ["-codec:a", codec]

        if formato_saida not in ("wav", "flac"):
            args += ["-b:a", bitrate]

        args.append(caminho_saida)

        return _run_ffmpeg(args)
    finally:
        try:
            if os.path.exists(lista_path):
                os.remove(lista_path)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# 4. VOLUME BOOSTER & NORMALIZER
# ─────────────────────────────────────────────────────────────────────────────

DB_OPCOES_VALIDAS = ["+3", "+6", "+12", "+18", "-3", "-6", "-12", "normalizar"]


def ajustar_volume(
    caminho_entrada: str,
    caminho_saida: str,
    ajuste: str = "+6"
) -> tuple[bool, str]:
    """
    Aumenta/diminui o volume ou normaliza o áudio.

    Args:
        caminho_entrada: Arquivo de entrada.
        caminho_saida: Arquivo de saída.
        ajuste: "+3", "+6", "+12", "+18", "-3", "-6", "-12" (dB) ou "normalizar".

    Returns:
        (True, "") em sucesso, ou (False, mensagem_erro).
    """
    ext_saida = os.path.splitext(caminho_saida)[1].lstrip(".").lower()
    codec = _CODEC_MAP.get(ext_saida, "libmp3lame")

    if ajuste == "normalizar":
        # Normalização loudnorm (EBU R128): dois passes
        # Passe 1: análise
        args_analise = [
            "-i", caminho_entrada,
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
            "-f", "null",
            "-"
        ]
        log.info("[volume] Analisando loudness para normalização...")
        result = subprocess.run(
            ["ffmpeg", "-y"] + args_analise,
            capture_output=True, text=True, timeout=120
        )
        stderr = result.stderr

        # Extrai parâmetros do JSON embutido no stderr
        import re, json
        match = re.search(r'\{[^{}]*"input_i"[^{}]*\}', stderr, re.DOTALL)
        if match:
            try:
                loudnorm_data = json.loads(match.group())
                af = (
                    f"loudnorm=I=-16:TP=-1.5:LRA=11:"
                    f"measured_I={loudnorm_data['input_i']}:"
                    f"measured_TP={loudnorm_data['input_tp']}:"
                    f"measured_LRA={loudnorm_data['input_lra']}:"
                    f"measured_thresh={loudnorm_data['input_thresh']}:"
                    f"offset={loudnorm_data['target_offset']}:linear=true:print_format=summary"
                )
            except Exception:
                af = "loudnorm=I=-16:TP=-1.5:LRA=11"
        else:
            af = "loudnorm=I=-16:TP=-1.5:LRA=11"

        args = [
            "-i", caminho_entrada,
            "-af", af,
            "-codec:a", codec,
            "-b:a", "192k",
            "-vn",
            caminho_saida
        ]
    else:
        # Ajuste de dB simples
        try:
            db_val = float(ajuste.replace("+", "").replace("dB", "").strip())
        except ValueError:
            return False, f"Ajuste de volume inválido: '{ajuste}'"

        af = f"volume={db_val}dB"
        args = [
            "-i", caminho_entrada,
            "-af", af,
            "-codec:a", codec,
            "-b:a", "192k",
            "-vn",
            caminho_saida
        ]

    return _run_ffmpeg(args)


# ─────────────────────────────────────────────────────────────────────────────
# 5. SPEED CHANGER (Time-Stretch sem alterar pitch)
# ─────────────────────────────────────────────────────────────────────────────

VELOCIDADE_MIN = 0.5
VELOCIDADE_MAX = 2.0


def alterar_velocidade(
    caminho_entrada: str,
    caminho_saida: str,
    fator: float = 1.5
) -> tuple[bool, str]:
    """
    Altera a velocidade do áudio SEM alterar o pitch (time-stretch).

    O filtro 'atempo' do FFmpeg aceita valores entre 0.5 e 2.0.
    Para fatores fora desse intervalo, encadeia múltiplos filtros atempo.

    Args:
        caminho_entrada: Arquivo de entrada.
        caminho_saida: Arquivo de saída.
        fator: Fator de velocidade (0.5x = metade, 2.0x = dobro).

    Returns:
        (True, "") em sucesso, ou (False, mensagem_erro).
    """
    if not (VELOCIDADE_MIN <= fator <= VELOCIDADE_MAX):
        return False, f"Fator de velocidade deve estar entre {VELOCIDADE_MIN}x e {VELOCIDADE_MAX}x."

    ext_saida = os.path.splitext(caminho_saida)[1].lstrip(".").lower()
    codec = _CODEC_MAP.get(ext_saida, "libmp3lame")

    # atempo aceita 0.5–2.0; para valores extremos encadeia filtros
    filtros = _construir_filtro_atempo(fator)
    af = ",".join(filtros)

    args = [
        "-i", caminho_entrada,
        "-af", af,
        "-codec:a", codec,
        "-b:a", "192k",
        "-vn",
        caminho_saida
    ]

    return _run_ffmpeg(args)


def _construir_filtro_atempo(fator: float) -> list:
    """Constrói lista de filtros atempo encadeados para o fator dado."""
    filtros = []
    fator_restante = fator
    while fator_restante > 2.0:
        filtros.append("atempo=2.0")
        fator_restante /= 2.0
    while fator_restante < 0.5:
        filtros.append("atempo=0.5")
        fator_restante /= 0.5
    filtros.append(f"atempo={fator_restante:.4f}")
    return filtros


# ─────────────────────────────────────────────────────────────────────────────
# 6. AUDIO REVERSER
# ─────────────────────────────────────────────────────────────────────────────

def inverter_audio(
    caminho_entrada: str,
    caminho_saida: str
) -> tuple[bool, str]:
    """
    Inverte o áudio (toca de trás para frente).

    Args:
        caminho_entrada: Arquivo de entrada.
        caminho_saida: Arquivo de saída.

    Returns:
        (True, "") em sucesso, ou (False, mensagem_erro).
    """
    ext_saida = os.path.splitext(caminho_saida)[1].lstrip(".").lower()
    codec = _CODEC_MAP.get(ext_saida, "libmp3lame")

    args = [
        "-i", caminho_entrada,
        "-af", "areverse",
        "-codec:a", codec,
        "-b:a", "192k",
        "-vn",
        caminho_saida
    ]

    return _run_ffmpeg(args)


# ─────────────────────────────────────────────────────────────────────────────
# Utilitário: obter duração do áudio
# ─────────────────────────────────────────────────────────────────────────────

def obter_duracao(caminho: str) -> float:
    """
    Retorna a duração do áudio em segundos usando ffprobe.
    Retorna 0.0 se não conseguir determinar.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                caminho
            ],
            capture_output=True, text=True, timeout=15
        )
        duracao = float(result.stdout.strip())
        return duracao
    except Exception:
        return 0.0


def formatar_duracao(segundos: float) -> str:
    """Formata segundos para string MM:SS ou HH:MM:SS."""
    segundos = int(segundos)
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    if horas > 0:
        return f"{horas:02d}:{minutos:02d}:{segs:02d}"
    return f"{minutos:02d}:{segs:02d}"


# ─────────────────────────────────────────────────────────────────────────────
# 7. AUDIO TRANSCRIBER (SPEECH-TO-TEXT)
# ─────────────────────────────────────────────────────────────────────────────

def _formatar_srt_tempo(segundos: float) -> str:
    """Formata segundos para o padrão de legendas SRT (00:00:00,000)."""
    millis = int((segundos - int(segundos)) * 1000)
    seg = int(segundos)
    hrs = seg // 3600
    mins = (seg % 3600) // 60
    segs = seg % 60
    return f"{hrs:02d}:{mins:02d}:{segs:02d},{millis:03d}"


_whisper_model_cache = {}


def _transcrever_com_whisper(wav_file: str, idioma: str = "auto", modelo_ia: str = "small") -> tuple[bool, str, list, list]:
    """
    Transcreve áudio com alta precisão neural utilizando o Whisper AI (OpenAI/Faster-Whisper).
    Possui filtro VAD (Voice Activity Detection) para ignorar trilhas sonoras e músicas de fundo.
    Modelos suportados: 'base', 'small', 'medium', 'large-v3'.
    """
    try:
        from faster_whisper import WhisperModel

        lang_code = None if idioma.lower() == "auto" else idioma.lower()
        if lang_code == "auto":
            lang_code = None

        m_size = modelo_ia.lower().strip() if modelo_ia else "small"
        if m_size not in ["base", "small", "medium", "large-v3", "turbo"]:
            m_size = "small"

        if m_size not in _whisper_model_cache:
            log.info(f"[whisper] Carregando modelo Whisper AI '{m_size}'...")
            _whisper_model_cache[m_size] = WhisperModel(m_size, device="cpu", compute_type="int8")

        model = _whisper_model_cache[m_size]
        segments, info = model.transcribe(
            wav_file,
            language=lang_code,
            beam_size=5,
            best_of=5,
            temperature=0.0,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        text_segments = []
        json_segments = []
        srt_blocks = []
        seq = 1

        for segment in list(segments):
            txt = segment.text.strip()
            if txt:
                text_segments.append(txt)
                t_start = _formatar_srt_tempo(segment.start)
                t_end = _formatar_srt_tempo(segment.end)
                srt_blocks.append(f"{seq}\n{t_start} --> {t_end}\n{txt}\n")
                json_segments.append({
                    "segmento": seq,
                    "inicio": round(segment.start, 2),
                    "fim": round(segment.end, 2),
                    "texto": txt
                })
                seq += 1

        texto_completo = " ".join(text_segments).strip()
        return True, texto_completo, srt_blocks, json_segments
    except Exception as e:
        log.warning(f"[whisper] Falha/fallback na transcrição neural com Whisper ({modelo_ia}): {e}")
        return False, str(e), [], []


def _transcrever_chunk_worker(args):
    """
    Worker paralelo fallback para reconhecer um trecho de áudio.
    """
    idx, offset, duration_sec, wav_file, lang_code = args
    import speech_recognition as sr

    r = sr.Recognizer()
    r.energy_threshold = 200
    r.dynamic_energy_threshold = True

    try:
        with sr.AudioFile(wav_file) as source:
            audio_chunk = r.record(source, offset=offset, duration=duration_sec)
            t_chunk = r.recognize_google(audio_chunk, language=lang_code).strip()
            return idx, offset, duration_sec, t_chunk, None
    except sr.UnknownValueError:
        return idx, offset, duration_sec, "", None
    except Exception as e:
        return idx, offset, duration_sec, "", str(e)


def transcrever_audio(
    caminho_entrada: str,
    caminho_saida: str,
    idioma: str = "auto",
    formato_saida: str = "txt",
    modelo_ia: str = "small"
) -> tuple[bool, str, str]:
    """
    Realiza a transcrição de áudio com inteligência artificial neural de alta precisão (Whisper AI Small/Medium),
    com pontuação perfeita, filtro de ruídos e fundo musical, e fallback paralelo.

    Args:
        caminho_entrada: Arquivo de entrada.
        caminho_saida: Caminho final do arquivo baixável.
        idioma: "auto", "pt", "en", "es".
        formato_saida: "txt", "srt", "json".
        modelo_ia: "base", "small", "medium".

    Returns:
        (sucesso: bool, mensagem_erro: str, texto_transcrito: str)
    """
    wav_temp = caminho_entrada + ".temp16k.wav"
    try:
        # Step 1: Pré-processamento otimizado do áudio via FFmpeg (16kHz mono pcm_s16le)
        args_wav = [
            "-i", caminho_entrada,
            "-ar", "16000",
            "-ac", "1",
            "-af", "highpass=f=120,lowpass=f=3800",
            "-codec:a", "pcm_s16le",
            "-vn",
            wav_temp
        ]
        ok_wav, msg_wav = _run_ffmpeg(args_wav)
        if not ok_wav:
            # Fallback sem filtros
            args_wav_simple = [
                "-i", caminho_entrada,
                "-ar", "16000",
                "-ac", "1",
                "-codec:a", "pcm_s16le",
                "-vn",
                wav_temp
            ]
            ok_wav, msg_wav = _run_ffmpeg(args_wav_simple)
            if not ok_wav:
                return False, f"Falha na conversão do áudio para pré-processamento: {msg_wav}", ""

        total_dur = obter_duracao(caminho_entrada)
        fmt = formato_saida.lower()

        lang_map = {
            "pt": "pt-BR",
            "en": "en-US",
            "es": "es-ES",
            "auto": "pt-BR"
        }
        lang_code = lang_map.get(idioma.lower(), "pt-BR")

        # Step 2: Tentativa 1 — Transcrição Neural com OpenAI Whisper AI (Modelo de Alta Precisão)
        ok_w, texto_completo, srt_blocks, json_segments = _transcrever_com_whisper(wav_temp, idioma, modelo_ia)

        # Step 2 Fallback: Se o Whisper falhar, usa transcrição paralela via SpeechRecognition
        if not ok_w or not texto_completo:
            log.info("[transcritor] Usando fallback paralelo de transcrição...")
            from concurrent.futures import ThreadPoolExecutor

            chunk_duration = 20
            tasks = []
            offset = 0.0
            segment_idx = 1
            while offset < (total_dur or 3600):
                current_chunk_len = min(chunk_duration, total_dur - offset) if total_dur > 0 else chunk_duration
                if current_chunk_len <= 0.5:
                    break
                tasks.append((segment_idx, offset, current_chunk_len, wav_temp, lang_code))
                offset += chunk_duration
                segment_idx += 1
                if total_dur == 0 and segment_idx > 30:
                    break

            max_workers = min(8, max(1, len(tasks)))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                raw_results = list(executor.map(_transcrever_chunk_worker, tasks))

            raw_results.sort(key=lambda x: x[0])

            text_segments = []
            srt_blocks = []
            json_segments = []
            seq_num = 1

            for idx, seg_offset, seg_len, t_chunk, err in raw_results:
                if t_chunk:
                    text_segments.append(t_chunk)
                    t_start = _formatar_srt_tempo(seg_offset)
                    t_end = _formatar_srt_tempo(seg_offset + seg_len)
                    srt_blocks.append(f"{seq_num}\n{t_start} --> {t_end}\n{t_chunk}\n")
                    json_segments.append({
                        "segmento": seq_num,
                        "inicio": round(seg_offset, 2),
                        "fim": round(seg_offset + seg_len, 2),
                        "texto": t_chunk
                    })
                    seq_num += 1

            texto_completo = " ".join(text_segments).strip()

        if not texto_completo:
            texto_completo = "Nenhuma fala audível ou inteligível foi detectada no arquivo enviado."

        fmt = formato_saida.lower()

        # Step 3: Formatação final do arquivo de saída
        conteudo_arquivo = ""
        if fmt == "srt":
            if srt_blocks:
                conteudo_arquivo = "\n".join(srt_blocks)
            else:
                t_inicio = _formatar_srt_tempo(0)
                t_fim = _formatar_srt_tempo(total_dur if total_dur > 0 else 10)
                conteudo_arquivo = f"1\n{t_inicio} --> {t_fim}\n{texto_completo}\n"
        elif fmt == "json":
            import json
            dados = {
                "ok": True,
                "transcricao": texto_completo,
                "idioma": lang_code,
                "duracao_segundos": round(total_dur, 2),
                "segmentos": json_segments,
                "motor": "Prisma Audio High-Speed Parallel STT Engine"
            }
            conteudo_arquivo = json.dumps(dados, ensure_ascii=False, indent=2)
        else:  # txt
            conteudo_arquivo = (
                f"==================================================\n"
                f" TRANSCRIÇÃO DE ÁUDIO — PRISMA AUDIO\n"
                f"==================================================\n"
                f"Idioma: {lang_code} | Duração: {formatar_duracao(total_dur)}\n\n"
                f"{texto_completo}\n"
            )

        with open(caminho_saida, "w", encoding="utf-8") as f:
            f.write(conteudo_arquivo)

        return True, "", texto_completo

    except Exception as e:
        log.exception("[transcritor] Exceção inesperada durante transcrição")
        return False, f"Erro no processamento da transcrição: {str(e)}", ""

    finally:
        if os.path.exists(wav_temp):
            try:
                os.remove(wav_temp)
            except Exception:
                pass
