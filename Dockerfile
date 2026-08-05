FROM python:3.11-slim-bookworm

# Instala LibreOffice (headless), Tesseract OCR e dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    fonts-dejavu \
    fonts-liberation \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    ffmpeg \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependências Python primeiro (aproveita cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do projeto
COPY . .

# Cria as pastas que o app usa em runtime, caso não existam
RUN mkdir -p uploads downloads

# Cria usuário não-privilegiado e ajusta permissões
RUN useradd -m appuser && \
    chown -R appuser:appuser /app uploads downloads

USER appuser
ENV HOME=/home/appuser

# ── Porta ────────────────────────────────────────────────────────────────────
# O Cloud Run injeta PORT dinamicamente (padrão 8080)
ENV PORT=8080
EXPOSE 8080

# ── Prevenção de deadlocks (libs C++ multi-thread: OpenCV, NumPy) ─────────────
ENV OMP_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV VECLIB_MAXIMUM_THREADS=1
ENV PYTHONUNBUFFERED=1
ENV NUMEXPR_NUM_THREADS=1

# ── Worker ───────────────────────────────────────────────────────────────────
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --threads 4 --timeout 120 app:app"]

