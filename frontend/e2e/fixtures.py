"""Gera os arquivos usados nos testes de navegador em frontend/e2e/.fixtures (fora do git)."""
import subprocess
from pathlib import Path

import pymupdf
import pandas as pd
import qrcode
from PIL import Image

d = Path(__file__).parent / ".fixtures"
d.mkdir(exist_ok=True)


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], check=True)


if not (d / "longo.mp4").exists():
    ffmpeg("-f", "lavfi", "-i", "sine=f=440:d=3", "-b:a", "128k", str(d / "a.mp3"))
    ffmpeg("-f", "lavfi", "-i", "testsrc=d=3:s=320x240:r=10", "-f", "lavfi", "-i", "sine=d=3",
           "-pix_fmt", "yuv420p", "-shortest", str(d / "v.mp4"))
    # Demora o bastante na compressão para dar tempo de cancelar.
    ffmpeg("-f", "lavfi", "-i", "testsrc2=d=120:s=1280x720:r=30", "-f", "lavfi", "-i", "sine=d=120",
           "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-shortest", str(d / "longo.mp4"))

Image.new("RGB", (300, 300), (200, 30, 30)).save(d / "i.png")
qrcode.make('<img src=x onerror="window.__xss=1">').save(d / "xss.png")
df = pd.DataFrame({"a": [1, 2], "b": ["<script>window.__xss=1</script>", "y"]})
df.to_csv(d / "t.csv", index=False)
df.to_excel(d / "t.xlsx", index=False)
pdf = pymupdf.open()
for i in range(3):
    pagina = pdf.new_page()
    pagina.insert_text((72, 72), f"pagina {i + 1}")
    pagina.insert_image(pymupdf.Rect(72, 100, 272, 300), filename=str(d / "i.png"))
pdf.save(d / "p.pdf")
pdf.save(d / "p2.pdf")
pdf.close()
