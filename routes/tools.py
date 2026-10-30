"""routes/tools.py — QR Code e paleta de cores."""
import re

from flask import Blueprint

from core.errors import ErroUsuario
from core.security import EXT_IMAGEM
from core.tarefas import executar_tarefa
from routes.pipeline import Contexto, Ferramenta, numero, registrar

tools_bp = Blueprint("tools", __name__)
_COR = re.compile(r"^#[0-9a-fA-F]{6}$")


def _validar_qr(form) -> dict:
    texto = (form.get("texto") or "").strip()
    if not texto:
        raise ErroUsuario("Digite um texto ou URL para gerar o QR Code.")
    if len(texto) > 2500:
        raise ErroUsuario("O texto é longo demais para um QR Code.")
    frente, fundo = form.get("cor_frente") or "#000000", form.get("cor_fundo") or "#FFFFFF"
    if not _COR.match(frente) or not _COR.match(fundo):
        raise ErroUsuario("Cor inválida.")
    return {"texto": texto, "cor_frente": frente, "cor_fundo": fundo}


def _gerar_qr(c: Contexto):
    executar_tarefa("qr.gerar", c.params["texto"], c.saida, cor_frente=c.params["cor_frente"],
                    cor_fundo=c.params["cor_fundo"], controle=c.controle)


def _ler_qr(c: Contexto) -> dict:
    return {"dados": {"codigos": executar_tarefa("qr.ler", c.entrada, controle=c.controle)}}


def _paleta(c: Contexto) -> dict:
    return {"dados": {"paleta": executar_tarefa("imagem.paleta", c.entrada, n_cores=c.params["n_cores"], controle=c.controle)}}


registrar(tools_bp, "/api/qr/gerar", Ferramenta(
    campo=None, min_arquivos=0, validar=_validar_qr, trabalho=_gerar_qr,
    nome_saida=lambda _n, _p: "Prisma_QRCode.png", origem="TEXTO", destino="PNG",
))
registrar(tools_bp, "/api/qr/ler", Ferramenta(extensoes=EXT_IMAGEM, trabalho=_ler_qr, gera_arquivo=False))
registrar(tools_bp, "/api/img/paleta", Ferramenta(
    extensoes=EXT_IMAGEM, validar=lambda f: {"n_cores": int(numero(f, "n_cores", 8, 3, 16))},
    trabalho=_paleta, gera_arquivo=False,
))
