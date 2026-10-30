"""pipeline.py — O caminho único de toda ferramenta.

Salva os uploads, valida, cria o job e devolve 202. Cada ferramenta declara só o
que muda: quais arquivos aceita, como validar o formulário e o trabalho a executar.
"""
import logging
import os
import shutil
import uuid
from dataclasses import dataclass, field
from typing import Callable

from flask import Blueprint, jsonify, request

from core import config, settings
from core.errors import ErroUsuario
from core.jobs import Job, apagar, jobs
from core.security import nome_seguro, obter_extensao, validar_entrada

log = logging.getLogger(__name__)


@dataclass
class Contexto:
    """O que o trabalho de uma ferramenta recebe."""
    job: Job
    entradas: list[str]
    nomes: list[str]
    params: dict
    saida: str
    pasta_saida: str

    @property
    def entrada(self) -> str:
        return self.entradas[0]

    @property
    def controle(self):
        return self.job.controle

    @property
    def pares(self) -> list[list[str]]:
        return [list(p) for p in zip(self.entradas, self.nomes)]


@dataclass
class Ferramenta:
    trabalho: Callable[[Contexto], dict | None]
    campo: str | None = "arquivo"
    min_arquivos: int = 1
    max_arquivos: int = 200
    extensoes: set[str] | None = None
    validar: Callable[[dict], dict] = field(default=lambda form: {})
    nome_saida: Callable[[str, dict], str] | None = None
    origem: str | Callable[[str, dict], str] = ""
    destino: str | Callable[[str, dict], str] = ""
    # Ferramentas que só devolvem dados não geram arquivo nem linha no histórico.
    gera_arquivo: bool = True


def _valor(rotulo, ext: str, params: dict) -> str:
    return rotulo(ext, params) if callable(rotulo) else rotulo


def salvar_uploads(arquivos: list, pasta: str, extensoes: set[str] | None) -> tuple[list[str], list[str]]:
    """Grava em disco com nomes neutros: nomes iguais não colidem e nomes estranhos não importam."""
    os.makedirs(pasta, exist_ok=True)
    caminhos, nomes = [], []
    for i, arquivo in enumerate(arquivos):
        nome = nome_seguro(arquivo.filename)
        ext = obter_extensao(nome)
        if extensoes is not None and ext not in extensoes:
            aceitas = ", ".join(sorted(e.upper() for e in extensoes))
            raise ErroUsuario(f"Formato '{ext.upper() or 'desconhecido'}' não aceito aqui. Use: {aceitas}.")
        caminho = os.path.join(pasta, f"{i:03d}.{ext}" if ext else f"{i:03d}")
        arquivo.save(caminho)
        if extensoes is not None:
            validar_entrada(caminho, ext)
        caminhos.append(caminho)
        nomes.append(nome)
    return caminhos, nomes


def iniciar_ferramenta(f: Ferramenta):
    arquivos = []
    if f.campo:
        arquivos = [a for a in request.files.getlist(f.campo) if a and a.filename]
        if len(arquivos) < f.min_arquivos:
            quantidade = "pelo menos 1 arquivo" if f.min_arquivos == 1 else f"pelo menos {f.min_arquivos} arquivos"
            raise ErroUsuario(f"Selecione {quantidade}.")
        if len(arquivos) > f.max_arquivos:
            raise ErroUsuario(f"Máximo de {f.max_arquivos} arquivos por operação.")

    params = f.validar(request.form)
    uid = uuid.uuid4().hex
    pasta_entrada = str(config.UPLOAD_DIR / uid)
    pasta_saida = str(config.DOWNLOAD_DIR / uid)
    try:
        entradas, nomes = salvar_uploads(arquivos, pasta_entrada, f.extensoes)
    except Exception:
        apagar(pasta_entrada)
        raise

    primeiro = nomes[0] if nomes else ""
    ext = obter_extensao(primeiro)
    nome_saida = f.nome_saida(primeiro, params) if f.nome_saida else ""
    job = jobs.criar(
        nome_download=nome_saida, origem=_valor(f.origem, ext, params), destino=_valor(f.destino, ext, params),
        no_historico=f.gera_arquivo, politica=settings.politica_retencao(),
        pasta_entrada=pasta_entrada, pasta_saida=pasta_saida if f.gera_arquivo else None,
    )
    saida = os.path.join(pasta_saida, nome_saida or "saida")
    if f.gera_arquivo:
        os.makedirs(pasta_saida, exist_ok=True)
        job.caminho_saida = saida

    contexto = Contexto(job, entradas, nomes, params, saida, pasta_saida)
    jobs.submeter(job, lambda _j: f.trabalho(contexto))
    return jsonify({"ok": True, "job_id": job.id, "status_url": f"/api/jobs/{job.id}"}), 202


def registrar(bp: Blueprint, rota: str, ferramenta: Ferramenta) -> None:
    def view():
        try:
            return iniciar_ferramenta(ferramenta)
        except ErroUsuario as e:
            return jsonify({"erro": str(e)}), 400
        except OSError:
            log.exception("Falha ao salvar upload em %s", rota)
            livre = shutil.disk_usage(config.DATA_DIR).free
            msg = "Sem espaço em disco." if livre < 50 * 1024 * 1024 else "Não foi possível salvar o arquivo enviado."
            return jsonify({"erro": msg}), 500

    bp.add_url_rule(rota, endpoint=rota.strip("/").replace("/", "_").replace("-", "_"), view_func=view, methods=["POST"])


def base_do_nome(nome: str) -> str:
    return os.path.splitext(nome)[0] or "arquivo"


def numero(form, campo: str, padrao: float, minimo: float, maximo: float) -> float:
    """Lê um número do formulário, recusando NaN/infinito e valores fora da faixa."""
    bruto = (form.get(campo) or "").strip()
    if not bruto:
        return padrao
    try:
        valor = float(bruto.replace(",", "."))
    except ValueError:
        raise ErroUsuario(f"Valor inválido em '{campo}'.") from None
    if not minimo <= valor <= maximo:  # também falha para NaN
        raise ErroUsuario(f"'{campo}' deve estar entre {minimo:g} e {maximo:g}.")
    return valor


def opcao(form, campo: str, permitidas, padrao: str) -> str:
    valor = (form.get(campo) or "").strip().lower()
    return valor if valor in permitidas else padrao
