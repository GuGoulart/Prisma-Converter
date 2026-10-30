"""routes/audio.py — Ferramentas de áudio."""
from flask import Blueprint

from core import audio_processor as ap
from core.config import TIMEOUT_TRANSCRICAO
from core.errors import ErroUsuario
from core.security import EXT_AUDIO
from core.tarefas import executar_tarefa
from routes.pipeline import Contexto, Ferramenta, base_do_nome, numero, opcao, registrar

audio_bp = Blueprint("audio", __name__)


def _validar_converter(form) -> dict:
    return {
        "formato": opcao(form, "formato", ap.FORMATOS_SUPORTADOS, "mp3"),
        "bitrate": opcao(form, "bitrate", ap.BITRATES_SUPORTADOS, "192k"),
        "canais": int(opcao(form, "canais", ("1", "2"), "2")),
        "sample_rate": int(opcao(form, "sample_rate", ("44100", "48000"), "44100")),
    }


def _converter(c: Contexto):
    ap.converter_audio(c.entrada, c.saida, c.params["formato"], c.params["bitrate"],
                       c.params["canais"], c.params["sample_rate"], c.controle)


def _validar_cortar(form) -> dict:
    inicio = ap.parse_tempo(form.get("inicio") or "0")
    fim = (form.get("fim") or "").strip()
    fim_s = ap.parse_tempo(fim) if fim else None
    if fim_s is not None and fim_s <= inicio:
        raise ErroUsuario("O tempo final deve ser maior que o tempo inicial.")
    return {"inicio": inicio, "fim": fim_s}


def _validar_juntar(form) -> dict:
    return {"formato": opcao(form, "formato", ap.FORMATOS_SUPORTADOS, "mp3"),
            "bitrate": opcao(form, "bitrate", ap.BITRATES_SUPORTADOS, "192k")}


def _validar_volume(form) -> dict:
    ajuste = (form.get("ajuste") or "+6").strip()
    if ajuste not in ap.AJUSTES_VOLUME:
        raise ErroUsuario("Ajuste de volume inválido.")
    return {"ajuste": ajuste}


def _sufixo_volume(ajuste: str) -> str:
    return "normalizado" if ajuste == "normalizar" else f"{ajuste}dB"


def _validar_velocidade(form) -> dict:
    return {"fator": numero(form, "fator", 1.5, ap.VELOCIDADE_MIN, ap.VELOCIDADE_MAX)}


def _validar_transcrever(form) -> dict:
    return {"idioma": opcao(form, "idioma", ("auto", "pt", "en", "es"), "auto"),
            "formato": opcao(form, "formato", ("txt", "srt", "json"), "txt"),
            "modelo": opcao(form, "modelo", ap.MODELOS_WHISPER, "small")}


def _transcrever(c: Contexto):
    dados = executar_tarefa("audio.transcrever", c.entrada, c.saida, c.params["idioma"], c.params["formato"],
                            c.params["modelo"], controle=c.controle, timeout=TIMEOUT_TRANSCRICAO)
    return {"dados": dados}


def _rotulo_ext(ext, _p):
    return ext.upper()


registrar(audio_bp, "/api/converter", Ferramenta(
    extensoes=EXT_AUDIO, validar=_validar_converter, trabalho=_converter,
    nome_saida=lambda n, p: f"{base_do_nome(n)}.{p['formato']}",
    origem=_rotulo_ext, destino=lambda _e, p: p["formato"].upper(),
))
registrar(audio_bp, "/api/cortar", Ferramenta(
    extensoes=EXT_AUDIO, validar=_validar_cortar,
    trabalho=lambda c: ap.cortar_audio(c.entrada, c.saida, c.params["inicio"], c.params["fim"], c.controle),
    nome_saida=lambda n, _p: f"{base_do_nome(n)}_cortado.{n.rsplit('.', 1)[-1]}",
    origem=_rotulo_ext, destino=lambda e, _p: f"{e.upper()} (CORTE)",
))
registrar(audio_bp, "/api/juntar", Ferramenta(
    campo="arquivos", min_arquivos=2, max_arquivos=50, extensoes=EXT_AUDIO, validar=_validar_juntar,
    trabalho=lambda c: ap.juntar_audios(c.entradas, c.saida, c.params["formato"], c.params["bitrate"], c.controle),
    nome_saida=lambda _n, p: f"prisma_juntados.{p['formato']}",
    origem="ÁUDIOS", destino=lambda _e, p: p["formato"].upper(),
))
registrar(audio_bp, "/api/volume", Ferramenta(
    extensoes=EXT_AUDIO, validar=_validar_volume,
    trabalho=lambda c: ap.ajustar_volume(c.entrada, c.saida, c.params["ajuste"], c.controle),
    nome_saida=lambda n, p: f"{base_do_nome(n)}_{_sufixo_volume(p['ajuste'])}.{n.rsplit('.', 1)[-1]}",
    origem=_rotulo_ext, destino=lambda e, _p: f"{e.upper()} (VOL)",
))
registrar(audio_bp, "/api/velocidade", Ferramenta(
    extensoes=EXT_AUDIO, validar=_validar_velocidade,
    trabalho=lambda c: ap.alterar_velocidade(c.entrada, c.saida, c.params["fator"], c.controle),
    nome_saida=lambda n, p: f"{base_do_nome(n)}_{p['fator']:.2f}x.{n.rsplit('.', 1)[-1]}",
    origem=_rotulo_ext, destino=lambda e, p: f"{e.upper()} ({p['fator']:.2f}x)",
))
registrar(audio_bp, "/api/inverter", Ferramenta(
    extensoes=EXT_AUDIO,
    trabalho=lambda c: ap.inverter_audio(c.entrada, c.saida, c.controle),
    nome_saida=lambda n, _p: f"{base_do_nome(n)}_invertido.{n.rsplit('.', 1)[-1]}",
    origem=_rotulo_ext, destino=lambda e, _p: f"{e.upper()} (REVERSO)",
))
registrar(audio_bp, "/api/transcrever", Ferramenta(
    extensoes=EXT_AUDIO, validar=_validar_transcrever, trabalho=_transcrever,
    nome_saida=lambda n, p: f"transcricao_{base_do_nome(n)}.{p['formato']}",
    origem=_rotulo_ext, destino=lambda _e, p: p["formato"].upper(),
))
