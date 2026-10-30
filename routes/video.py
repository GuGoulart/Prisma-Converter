"""routes/video.py — Ferramentas de vídeo e download por link."""
from flask import Blueprint

from core import video_processor as vp
from core.errors import ErroUsuario
from core.security import EXT_VIDEO
from core.video_downloader import baixar_video_por_link
from routes.pipeline import Contexto, Ferramenta, base_do_nome, numero, opcao, registrar

video_bp = Blueprint("video", __name__)


def _rotulo_ext(ext, _p):
    return ext.upper()


def _validar_gif(form) -> dict:
    return {"inicio": numero(form, "inicio", 0, 0, 86400), "duracao": numero(form, "duracao", 5, 0.1, 600),
            "fps": int(numero(form, "fps", 10, 1, 30)), "largura": int(numero(form, "largura", 480, 160, 1080))}


def _validar_foto(form) -> dict:
    return {"tempo": numero(form, "tempo", 1, 0, 86400), "formato": opcao(form, "formato", ("png", "jpg", "jpeg"), "png")}


def _validar_link(form) -> dict:
    url = (form.get("url") or "").strip()
    if not url:
        raise ErroUsuario("Cole a URL do vídeo.")
    return {"url": url, "formato": opcao(form, "formato", ("mp4", "mp3"), "mp4"), "qualidade": (form.get("qualidade") or "best").strip().lower()}


def _baixar(c: Contexto) -> dict:
    caminho, nome = baixar_video_por_link(c.params["url"], c.pasta_saida, c.params["formato"], c.params["qualidade"], c.controle)
    return {"caminho": caminho, "nome_download": nome}


registrar(video_bp, "/api/video/mp4-para-mp3", Ferramenta(
    extensoes=EXT_VIDEO, validar=lambda f: {"bitrate": opcao(f, "bitrate", vp.BITRATES_MP3, "192k")},
    trabalho=lambda c: vp.converter_mp4_para_mp3(c.entrada, c.saida, c.params["bitrate"], c.controle),
    nome_saida=lambda n, _p: f"{base_do_nome(n)}.mp3", origem=_rotulo_ext, destino="MP3",
))
registrar(video_bp, "/api/video/mp4-para-gif", Ferramenta(
    extensoes=EXT_VIDEO, validar=_validar_gif,
    trabalho=lambda c: vp.converter_mp4_para_gif(c.entrada, c.saida, c.params["inicio"], c.params["duracao"],
                                                 c.params["fps"], c.params["largura"], c.controle),
    nome_saida=lambda n, _p: f"{base_do_nome(n)}.gif", origem=_rotulo_ext, destino="GIF",
))
registrar(video_bp, "/api/video/converter", Ferramenta(
    extensoes=EXT_VIDEO, validar=lambda f: {"formato": opcao(f, "formato", vp.FORMATOS_SAIDA, "mp4")},
    trabalho=lambda c: vp.converter_formato_video(c.entrada, c.saida, c.params["formato"], c.controle),
    nome_saida=lambda n, p: f"{base_do_nome(n)}_convertido.{p['formato']}",
    origem=_rotulo_ext, destino=lambda _e, p: p["formato"].upper(),
))
registrar(video_bp, "/api/video/compressor", Ferramenta(
    extensoes=EXT_VIDEO, validar=lambda f: {"nivel": opcao(f, "nivel", vp.NIVEIS_COMPRESSAO, "medio")},
    trabalho=lambda c: vp.compressor_video(c.entrada, c.saida, c.params["nivel"], c.controle),
    nome_saida=lambda n, _p: f"{base_do_nome(n)}_comprimido.mp4",
    origem=_rotulo_ext, destino=lambda _e, p: f"MP4 ({p['nivel'].upper()})",
))
registrar(video_bp, "/api/video/remover-audio", Ferramenta(
    extensoes=EXT_VIDEO,
    trabalho=lambda c: vp.remover_audio_video(c.entrada, c.saida, c.controle),
    nome_saida=lambda n, _p: f"{base_do_nome(n)}_sem_audio.{n.rsplit('.', 1)[-1]}",
    origem=_rotulo_ext, destino=lambda e, _p: f"{e.upper()} (MUDO)",
))
registrar(video_bp, "/api/video/capturar-foto", Ferramenta(
    extensoes=EXT_VIDEO, validar=_validar_foto,
    trabalho=lambda c: vp.capturar_foto_video(c.entrada, c.saida, c.params["tempo"], c.controle),
    nome_saida=lambda n, p: f"{base_do_nome(n)}_foto.{p['formato']}",
    origem=_rotulo_ext, destino=lambda _e, p: p["formato"].upper(),
))
registrar(video_bp, "/api/video/baixar-link", Ferramenta(
    campo=None, min_arquivos=0, validar=_validar_link, trabalho=_baixar,
    nome_saida=lambda _n, p: f"download.{p['formato']}", origem="URL", destino=lambda _e, p: p["formato"].upper(),
))
