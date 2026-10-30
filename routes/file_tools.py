"""routes/file_tools.py — Compressão, criptografia, hash, renomeação e planilhas."""
import re

from flask import Blueprint

from core.errors import ErroUsuario
from core.security import EXT_PLANILHA
from core.tarefas import executar_tarefa
from routes.pipeline import Contexto, Ferramenta, opcao, registrar

file_tools_bp = Blueprint("file_tools", __name__)


def _senha(form) -> dict:
    senha = form.get("senha") or ""
    if not senha.strip():
        raise ErroUsuario("A senha é obrigatória.")
    return {"senha": senha}


def _padrao_nome(form) -> dict:
    padrao = re.sub(r"[^\w\- {}]", "", form.get("padrao") or "").strip()[:100]
    return {"padrao": padrao or "arquivo_{n}"}


def _sem_enc(nome: str, _p) -> str:
    return nome[:-4] if nome.lower().endswith(".enc") else f"descriptografado_{nome}"


def _hash(c: Contexto) -> dict:
    dados = executar_tarefa("arquivo.hash", c.entrada, controle=c.controle)
    dados["nome"] = c.nomes[0]
    return {"dados": dados}


registrar(file_tools_bp, "/api/file/comprimir", Ferramenta(
    campo="arquivos",
    validar=lambda f: {"formato": opcao(f, "formato", ("zip", "tar.gz"), "zip")},
    trabalho=lambda c: executar_tarefa("arquivo.comprimir", c.pares, c.saida, c.params["formato"], controle=c.controle),
    nome_saida=lambda _n, p: f"Prisma_Comprimido.{p['formato']}", origem="ARQUIVOS",
    destino=lambda _e, p: p["formato"].upper(),
))
registrar(file_tools_bp, "/api/file/zip-senha", Ferramenta(
    campo="arquivos", validar=_senha,
    trabalho=lambda c: executar_tarefa("arquivo.zip_senha", c.pares, c.saida, c.params["senha"], controle=c.controle),
    nome_saida=lambda _n, _p: "Prisma_Protegido.zip", origem="ARQUIVOS", destino="ZIP",
))
registrar(file_tools_bp, "/api/file/criptografar", Ferramenta(
    validar=_senha,
    trabalho=lambda c: executar_tarefa("arquivo.criptografar", c.entrada, c.saida, c.params["senha"], controle=c.controle),
    nome_saida=lambda n, _p: f"{n}.enc", origem="ARQUIVO", destino="ENC",
))
registrar(file_tools_bp, "/api/file/descriptografar", Ferramenta(
    validar=_senha,
    trabalho=lambda c: executar_tarefa("arquivo.descriptografar", c.entrada, c.saida, c.params["senha"], controle=c.controle),
    nome_saida=_sem_enc, origem="ENC", destino="ARQUIVO",
))
registrar(file_tools_bp, "/api/file/hash", Ferramenta(trabalho=_hash, gera_arquivo=False))
registrar(file_tools_bp, "/api/file/renomear-lote", Ferramenta(
    campo="arquivos", validar=_padrao_nome,
    trabalho=lambda c: executar_tarefa("arquivo.renomear", c.pares, c.params["padrao"], c.saida, controle=c.controle),
    nome_saida=lambda _n, _p: "Prisma_Renomeados.zip", origem="ARQUIVOS", destino="ZIP",
))
registrar(file_tools_bp, "/api/data/mesclar-planilhas", Ferramenta(
    campo="arquivos", min_arquivos=2, extensoes=EXT_PLANILHA,
    validar=lambda f: {"formato": opcao(f, "formato", ("xlsx", "csv", "json"), "xlsx")},
    trabalho=lambda c: executar_tarefa("planilhas.mesclar", c.entradas, c.saida, c.params["formato"], controle=c.controle),
    nome_saida=lambda _n, p: f"Prisma_Planilhas_Mescladas.{p['formato']}", origem="PLANILHAS",
    destino=lambda _e, p: p["formato"].upper(),
))
