"""pdf_tools.py — Mesclar, dividir, proteger, comprimir, marcar e editar PDFs."""
import io
import logging
import os
import shutil
import zipfile

import pymupdf
from PIL import Image

from core.errors import ErroUsuario
from core.progresso import reportar

log = logging.getLogger(__name__)


def _abrir(caminho: str, senha: str | None = None) -> pymupdf.Document:
    try:
        doc = pymupdf.open(caminho)
    except Exception:
        raise ErroUsuario("Não foi possível abrir o PDF. O arquivo pode estar corrompido.") from None
    if doc.needs_pass:
        if senha is None:
            doc.close()
            raise ErroUsuario("Este PDF está protegido por senha. Use 'Desproteger PDF' primeiro.")
        if not doc.authenticate(senha):
            doc.close()
            raise ErroUsuario("Senha incorreta.")
    return doc


def _intervalos(texto: str, total: int) -> list[tuple[int, int]]:
    """Interpreta "1-3, 5" em intervalos de índices. Rejeita o que não entende."""
    intervalos = []
    for parte in filter(None, (p.strip() for p in texto.split(","))):
        try:
            inicio, _, fim = parte.partition("-")
            a, b = int(inicio), int(fim or inicio)
        except ValueError:
            raise ErroUsuario(f"Intervalo inválido: '{parte}'. Use o formato 1-3, 5, 7-10.") from None
        if a < 1 or b < a:
            raise ErroUsuario(f"Intervalo inválido: '{parte}'.")
        if a > total:
            raise ErroUsuario(f"A página {a} não existe: o documento tem {total} página(s).")
        intervalos.append((a - 1, min(b, total) - 1))
    return intervalos


def mesclar_pdfs(entradas: list, saida: str) -> None:
    if not entradas:
        raise ErroUsuario("Nenhum arquivo fornecido para mesclagem.")
    resultado = pymupdf.open()
    for i, caminho in enumerate(entradas):
        with _abrir(caminho) as doc:
            resultado.insert_pdf(doc)
        reportar((i + 1) / len(entradas) * 95)
    resultado.save(saida, garbage=3, deflate=True)
    resultado.close()


def dividir_pdf(entrada: str, saida_zip: str, modo: str = "individual", parametro: str = "") -> None:
    with _abrir(entrada) as doc:
        total = doc.page_count
        if modo == "fixo":
            try:
                passo = int(parametro)
            except ValueError:
                raise ErroUsuario("Informe quantas páginas cada parte deve ter.") from None
            if passo < 1:
                raise ErroUsuario("Cada parte precisa ter pelo menos 1 página.")
            intervalos = [(i, min(i + passo, total) - 1) for i in range(0, total, passo)]
        elif modo == "custom":
            intervalos = _intervalos(parametro, total)
            if not intervalos:
                raise ErroUsuario("Informe os intervalos no formato 1-3, 5, 7-10.")
        else:
            intervalos = [(i, i) for i in range(total)]

        with zipfile.ZipFile(saida_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, (inicio, fim) in enumerate(intervalos, start=1):
                parte = pymupdf.open()
                parte.insert_pdf(doc, from_page=inicio, to_page=fim)
                zf.writestr(f"parte_{idx}.pdf", parte.tobytes(garbage=3, deflate=True))
                parte.close()
                reportar(idx / len(intervalos) * 95)


def proteger_pdf(entrada: str, senha: str, saida: str) -> None:
    with _abrir(entrada) as doc:
        doc.save(saida, encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw=senha, user_pw=senha,
                 permissions=int(pymupdf.PDF_PERM_PRINT | pymupdf.PDF_PERM_COPY))


def desproteger_pdf(entrada: str, senha: str, saida: str) -> None:
    with _abrir(entrada, senha) as doc:
        doc.save(saida, encryption=pymupdf.PDF_ENCRYPT_NONE)


def comprimir_pdf(entrada: str, saida: str, nivel: str = "media") -> None:
    """Recomprime imagens e remove objetos redundantes. Nunca devolve algo maior que o original."""
    qualidade, lado_maximo = {"alta": (40, 1200), "media": (75, 2000)}.get(nivel, (None, None))
    with _abrir(entrada) as doc:
        if qualidade:
            _recomprimir_imagens(doc, qualidade, lado_maximo)
        doc.save(saida, garbage=4, deflate=True, clean=True)
    if os.path.getsize(saida) >= os.path.getsize(entrada):
        shutil.copy2(entrada, saida)


def _recomprimir_imagens(doc: pymupdf.Document, qualidade: int, lado_maximo: int) -> None:
    vistos: set[int] = set()
    total = len(doc) or 1
    for i, pagina in enumerate(doc):
        for info in pagina.get_images(full=True):
            xref, smask = info[0], info[1]
            # Imagens com transparência dependem do formato original.
            if xref in vistos or smask:
                continue
            vistos.add(xref)
            try:
                img = Image.open(io.BytesIO(doc.extract_image(xref)["image"]))
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.thumbnail((lado_maximo, lado_maximo), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=qualidade, optimize=True)
                if len(buffer.getvalue()) < len(doc.xref_stream_raw(xref) or b""):
                    pagina.replace_image(xref, stream=buffer.getvalue())
            except Exception as e:
                log.warning("Imagem %s mantida sem recompressão: %s", xref, e)
        reportar((i + 1) / total * 90)


def adicionar_marca_dagua(entrada: str, texto: str, saida: str) -> None:
    with _abrir(entrada) as doc:
        for pagina in doc:
            r = pagina.rect
            tamanho = min(72, min(r.width, r.height) / (max(len(texto), 1) * 0.5))
            pagina.insert_text(pymupdf.Point(r.width / 4, r.height / 2), texto, fontsize=tamanho,
                               color=(0.5, 0.5, 0.5), fill_opacity=0.3)
        doc.save(saida)


def extrair_imagens_pdf(entrada: str, saida_zip: str) -> None:
    vistos: set[int] = set()
    with _abrir(entrada) as doc, zipfile.ZipFile(saida_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for num, pagina in enumerate(doc):
            for info in pagina.get_images(full=True):
                xref = info[0]
                if xref in vistos:
                    continue
                vistos.add(xref)
                imagem = doc.extract_image(xref)
                zf.writestr(f"imagem_{len(vistos)}.{imagem['ext']}", imagem["image"])
            reportar((num + 1) / (len(doc) or 1) * 95)
    if not vistos:
        raise ErroUsuario("Este PDF não contém imagens para extrair.")


def manipular_paginas_pdf(entrada: str, saida: str, remover: str = "", rotacionar: str = "") -> None:
    """Remove páginas ("1, 3-5") e/ou rotaciona ("2:90, 4:180")."""
    if not remover.strip() and not rotacionar.strip():
        raise ErroUsuario("Informe as páginas a remover ou a rotacionar.")
    with _abrir(entrada) as doc:
        total = doc.page_count
        rotacoes: dict[int, int] = {}
        for parte in filter(None, (p.strip() for p in rotacionar.split(","))):
            try:
                pg, graus = (int(x) for x in parte.split(":"))
            except ValueError:
                raise ErroUsuario(f"Rotação inválida: '{parte}'. Use o formato 2:90, 4:180.") from None
            if not 1 <= pg <= total:
                raise ErroUsuario(f"A página {pg} não existe: o documento tem {total} página(s).")
            if graus % 90:
                raise ErroUsuario("A rotação precisa ser múltiplo de 90 graus.")
            rotacoes[pg - 1] = graus

        excluir = {i for a, b in _intervalos(remover, total) for i in range(a, b + 1)}
        manter = [i for i in range(total) if i not in excluir]
        if not manter:
            raise ErroUsuario("Essa operação deixaria o PDF sem páginas.")

        for indice, graus in rotacoes.items():
            pagina = doc[indice]
            pagina.set_rotation((pagina.rotation + graus) % 360)
        doc.select(manter)
        doc.save(saida, garbage=3, deflate=True)
