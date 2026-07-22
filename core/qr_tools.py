"""
qr_tools.py — Gerador e Leitor de QR Code.
Gera com qrcode[pil] e lê com OpenCV (cv2) ou pyzbar.
"""

import os
import logging

log = logging.getLogger(__name__)


def gerar_qrcode(
    texto: str,
    saida: str,
    formato: str = "png",
    cor_frente: str = "#000000",
    cor_fundo: str = "#FFFFFF",
    tamanho_box: int = 10,
    borda: int = 4,
):
    """
    Gera uma imagem de QR Code a partir de um texto ou URL.
    """
    try:
        import qrcode
    except ImportError:
        raise RuntimeError("Biblioteca 'qrcode' não instalada.")

    if not texto or not texto.strip():
        raise ValueError("O texto para o QR Code não pode ser vazio.")

    qr = qrcode.QRCode(
        version=None,  # Auto-detect
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=tamanho_box,
        border=borda,
    )
    qr.add_data(texto.strip())
    qr.make(fit=True)

    img = qr.make_image(
        fill_color=cor_frente,
        back_color=cor_fundo,
    )

    fmt_upper = formato.upper()
    if fmt_upper in ("JPG", "JPEG"):
        fmt_upper = "JPEG"
        if hasattr(img, "mode") and img.mode == "RGBA":
            from PIL import Image
            bg = Image.new("RGB", img.size, cor_fundo)
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif hasattr(img, "convert"):
            img = img.convert("RGB")

    os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
    img.save(saida, fmt_upper)
    log.info(f"QR Code gerado: {os.path.basename(saida)}")


def ler_qrcode(caminho_imagem: str) -> list:
    """
    Lê QR Codes de uma imagem. Usa OpenCV como método primário e pyzbar como fallback.

    Args:
        caminho_imagem: Caminho da imagem com QR Code(s).

    Returns:
        Lista de dicts com {"tipo": str, "dados": str} para cada código encontrado.
    """
    if not os.path.exists(caminho_imagem):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_imagem}")

    codigos = []

    # 1. Método Primário: OpenCV (Nativo em Python/C++, sem dependência de DLLs do zbar no Windows)
    try:
        import cv2
        img = cv2.imread(caminho_imagem)
        if img is not None:
            detector = cv2.QRCodeDetector()
            # Tentar decodificar múltiplos QR codes
            try:
                retval, decoded_info, points, straight_qrcode = detector.detectAndDecodeMulti(img)
                if retval and decoded_info:
                    for item in decoded_info:
                        if item and item.strip():
                            codigos.append({"tipo": "QRCODE", "dados": item.strip()})
            except Exception as e_multi:
                log.debug(f"OpenCV detectAndDecodeMulti error: {e_multi}")

            if not codigos:
                val, points, _ = detector.detectAndDecode(img)
                if val and val.strip():
                    codigos.append({"tipo": "QRCODE", "dados": val.strip()})
    except Exception as e_cv:
        log.warning(f"OpenCV QR decode error: {e_cv}")

    # 2. Fallback: pyzbar
    if not codigos:
        try:
            from pyzbar.pyzbar import decode
            from PIL import Image

            img_pil = Image.open(caminho_imagem)
            if img_pil.mode not in ("RGB", "L"):
                img_pil = img_pil.convert("RGB")

            resultados = decode(img_pil)
            for r in resultados:
                dados = r.data.decode("utf-8", errors="replace")
                if dados and dados.strip():
                    codigos.append({
                        "tipo": str(r.type),
                        "dados": dados.strip(),
                    })
        except Exception as e_zbar:
            log.warning(f"pyzbar QR decode error: {e_zbar}")

    if not codigos:
        raise ValueError(
            "Nenhum QR Code legível foi encontrado na imagem. "
            "Certifique-se de enviar uma imagem nítida contendo um QR Code."
        )

    log.info(f"QR lido com sucesso: {len(codigos)} código(s) em {os.path.basename(caminho_imagem)}")
    return codigos
