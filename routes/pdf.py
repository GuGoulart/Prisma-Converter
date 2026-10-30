"""routes/pdf.py — Ferramentas de PDF."""
from flask import Blueprint

from core.errors import ErroUsuario
from core.tarefas import executar_tarefa
from routes.pipeline import Contexto, Ferramenta, opcao, registrar

pdf_bp = Blueprint("pdf", __name__)
_PDF = {"pdf"}


def _obrigatorio(form, campo: str, mensagem: str) -> str:
    valor = form.get(campo) or ""
    if not valor.strip():
        raise ErroUsuario(mensagem)
    return valor


def _tarefa(nome: str, *chaves: str):
    """Trabalho simples: a tarefa recebe (entrada, saida, *parâmetros)."""
    def trabalho(c: Contexto):
        executar_tarefa(nome, c.entrada, c.saida, *(c.params[k] for k in chaves), controle=c.controle)
    return trabalho


def _senha(form) -> dict:
    return {"senha": _obrigatorio(form, "senha", "A senha é obrigatória.")}


registrar(pdf_bp, "/api/pdf/mesclar", Ferramenta(
    campo="arquivos", min_arquivos=2, extensoes=_PDF,
    trabalho=lambda c: executar_tarefa("pdf.mesclar", c.entradas, c.saida, controle=c.controle),
    nome_saida=lambda _n, _p: "Prisma_Mesclado.pdf", origem="PDF", destino="PDF",
))
registrar(pdf_bp, "/api/pdf/dividir", Ferramenta(
    extensoes=_PDF,
    validar=lambda f: {"modo": opcao(f, "modo", ("individual", "fixo", "custom"), "individual"),
                       "parametro": f.get("parametro") or ""},
    trabalho=_tarefa("pdf.dividir", "modo", "parametro"),
    nome_saida=lambda _n, _p: "Prisma_Dividido.zip", origem="PDF", destino="ZIP",
))
registrar(pdf_bp, "/api/pdf/proteger", Ferramenta(
    extensoes=_PDF, validar=_senha,
    trabalho=lambda c: executar_tarefa("pdf.proteger", c.entrada, c.params["senha"], c.saida, controle=c.controle),
    nome_saida=lambda _n, _p: "Prisma_Protegido.pdf", origem="PDF", destino="PDF",
))
registrar(pdf_bp, "/api/pdf/desproteger", Ferramenta(
    extensoes=_PDF, validar=_senha,
    trabalho=lambda c: executar_tarefa("pdf.desproteger", c.entrada, c.params["senha"], c.saida, controle=c.controle),
    nome_saida=lambda _n, _p: "Prisma_Desprotegido.pdf", origem="PDF", destino="PDF",
))
registrar(pdf_bp, "/api/pdf/comprimir", Ferramenta(
    extensoes=_PDF, validar=lambda f: {"nivel": opcao(f, "nivel", ("baixa", "media", "alta"), "media")},
    trabalho=_tarefa("pdf.comprimir", "nivel"),
    nome_saida=lambda _n, _p: "Prisma_Comprimido.pdf", origem="PDF", destino="PDF",
))
registrar(pdf_bp, "/api/pdf/marca-dagua", Ferramenta(
    extensoes=_PDF, validar=lambda f: {"texto": _obrigatorio(f, "texto", "Digite o texto da marca d'água.")[:200]},
    trabalho=lambda c: executar_tarefa("pdf.marca", c.entrada, c.params["texto"], c.saida, controle=c.controle),
    nome_saida=lambda _n, _p: "Prisma_Marcado.pdf", origem="PDF", destino="PDF",
))
registrar(pdf_bp, "/api/pdf/extrair-imagens", Ferramenta(
    extensoes=_PDF, trabalho=_tarefa("pdf.imagens"),
    nome_saida=lambda _n, _p: "Prisma_Imagens_PDF.zip", origem="PDF", destino="ZIP",
))
registrar(pdf_bp, "/api/pdf/manipular-paginas", Ferramenta(
    extensoes=_PDF, validar=lambda f: {"remover": f.get("remover") or "", "rotacionar": f.get("rotacionar") or ""},
    trabalho=_tarefa("pdf.paginas", "remover", "rotacionar"),
    nome_saida=lambda _n, _p: "Prisma_Paginas_Manipuladas.pdf", origem="PDF", destino="PDF",
))
