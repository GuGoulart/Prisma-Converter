"""
image_tools.py — Ferramentas avançadas de imagem.
Extração de paleta de cores.
"""

import os
import logging

log = logging.getLogger(__name__)


def extrair_paleta(caminho_imagem: str, n_cores: int = 8, tolerancia: int = 32) -> list:
    """
    Extrai as cores dominantes de uma imagem.

    Args:
        caminho_imagem: Caminho da imagem.
        n_cores: Número máximo de cores a retornar (3-16).
        tolerancia: Tolerância de agrupamento do extcolors.

    Returns:
        Lista de dicts: [{"hex": "#...", "rgb": "rgb(...)", "r": r, "g": g, "b": b, "percentual": p}, ...]
    """
    if not os.path.exists(caminho_imagem):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_imagem}")

    paleta = []

    # 1. Tentar extcolors
    try:
        import extcolors
        from PIL import Image

        img = Image.open(caminho_imagem)
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Redimensionar para acelerar extração
        max_lado = 250
        if max(img.size) > max_lado:
            ratio = max_lado / max(img.size)
            novo_tamanho = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(novo_tamanho, Image.Resampling.LANCZOS)

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
            img.save(tmp_path, "PNG")

        try:
            cores_extraidas, total_pixels = extcolors.extract_from_path(
                tmp_path,
                tolerance=tolerancia,
                limit=n_cores,
            )
            for (r, g, b), contagem in cores_extraidas[:n_cores]:
                percentual = round((contagem / total_pixels) * 100, 1) if total_pixels > 0 else 0
                hex_cor = f"#{r:02x}{g:02x}{b:02x}"
                paleta.append({
                    "hex": hex_cor,
                    "rgb": f"rgb({r}, {g}, {b})",
                    "r": r, "g": g, "b": b,
                    "percentual": percentual,
                })
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
    except Exception as e:
        log.warning(f"extcolors falhou ou ausente, usando fallback PIL: {e}")

    # 2. Fallback PIL se extcolors não estiver disponível ou falhar
    if not paleta:
        try:
            from PIL import Image
            img = Image.open(caminho_imagem).convert("RGB")
            img.thumbnail((200, 200))
            img_quant = img.quantize(colors=n_cores, method=Image.Quantize.FASTOCTREE)
            palette_colors = img_quant.getpalette()
            color_counts = sorted(img_quant.getcolors(maxcolors=256) or [], key=lambda x: x[0], reverse=True)
            total = sum(c[0] for c in color_counts) or 1

            for count, index in color_counts[:n_cores]:
                r = palette_colors[index * 3]
                g = palette_colors[index * 3 + 1]
                b = palette_colors[index * 3 + 2]
                percentual = round((count / total) * 100, 1)
                hex_cor = f"#{r:02x}{g:02x}{b:02x}"
                paleta.append({
                    "hex": hex_cor,
                    "rgb": f"rgb({r}, {g}, {b})",
                    "r": r, "g": g, "b": b,
                    "percentual": percentual,
                })
        except Exception as e_pil:
            log.warning(f"PIL palette extraction error: {e_pil}")

    if not paleta:
        raise ValueError("Não foi possível extrair as cores da imagem.")

    log.info(f"Paleta extraída: {len(paleta)} cores de {os.path.basename(caminho_imagem)}")
    return paleta
