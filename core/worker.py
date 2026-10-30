"""worker.py — Executa uma tarefa pesada em processo próprio.

Rodar em processo separado é o que permite cancelar e impor limite de tempo a
qualquer ferramenta, e isola a memória: quando a tarefa termina, tudo é devolvido.

Protocolo: JSON em stdin ({"tarefa", "args", "kwargs"}); no stdout, linhas
"@@PROGRESSO n", "@@AVISO texto" e, ao final, "@@RESULTADO json".
"""
import importlib
import json
import logging
import sys

TAREFAS = {
    "converter": "core.converter:converter_arquivo",
    "preview.imagem": "core.converter:gerar_preview_imagem",
    "planilhas.mesclar": "core.converter:mesclar_planilhas",
    "pdf.mesclar": "core.pdf_tools:mesclar_pdfs",
    "pdf.dividir": "core.pdf_tools:dividir_pdf",
    "pdf.proteger": "core.pdf_tools:proteger_pdf",
    "pdf.desproteger": "core.pdf_tools:desproteger_pdf",
    "pdf.comprimir": "core.pdf_tools:comprimir_pdf",
    "pdf.marca": "core.pdf_tools:adicionar_marca_dagua",
    "pdf.imagens": "core.pdf_tools:extrair_imagens_pdf",
    "pdf.paginas": "core.pdf_tools:manipular_paginas_pdf",
    "arquivo.comprimir": "core.file_tools:comprimir_arquivos",
    "arquivo.zip_senha": "core.file_tools:zip_com_senha",
    "arquivo.criptografar": "core.file_tools:criptografar_arquivo",
    "arquivo.descriptografar": "core.file_tools:descriptografar_arquivo",
    "arquivo.hash": "core.file_tools:calcular_hashes",
    "arquivo.renomear": "core.file_tools:renomear_em_lote",
    "qr.gerar": "core.qr_tools:gerar_qrcode",
    "qr.ler": "core.qr_tools:ler_qrcode",
    "imagem.paleta": "core.image_tools:extrair_paleta",
    "audio.transcrever": "core.audio_processor:transcrever_audio",
}


def _emitir(obj: dict) -> None:
    print("@@RESULTADO " + json.dumps(obj, ensure_ascii=False), flush=True)


def main() -> int:
    from core.errors import ErroUsuario

    logging.basicConfig(level=logging.WARNING, stream=sys.stderr,
                        format="%(levelname)s %(name)s: %(message)s")
    pedido = json.load(sys.stdin)
    modulo, funcao = TAREFAS[pedido["tarefa"]].split(":")
    try:
        alvo = getattr(importlib.import_module(modulo), funcao)
        valor = alvo(*pedido.get("args", []), **pedido.get("kwargs", {}))
        _emitir({"ok": True, "valor": valor})
        return 0
    except ErroUsuario as e:
        _emitir({"ok": False, "erro": str(e)})
        return 0
    except Exception:
        logging.exception("Falha na tarefa %s", pedido["tarefa"])
        _emitir({"ok": False, "erro": None})
        return 1


if __name__ == "__main__":
    sys.exit(main())
