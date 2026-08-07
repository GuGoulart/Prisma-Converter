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
# O Render injeta PORT dinamicamente (padrão 10000 no Render, 8080 fallback)
ENV PORT=10000
EXPOSE 10000

# ── Prevenção de deadlocks e estouro de RAM (libs C++ multi-thread: OpenCV, PyMuPDF, NumPy) ─
ENV OMP_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV VECLIB_MAXIMUM_THREADS=1
ENV PYTHONUNBUFFERED=1
ENV NUMEXPR_NUM_THREADS=1
ENV OPENCV_FOR_THREADS_NUM=1

# ── Worker ───────────────────────────────────────────────────────────────────
# Configuração otimizada para o Render:
# - 1 worker para minimizar uso de RAM (plano Starter: 512 MB)
# - 4 threads para servir requisições simultâneas sem overhead de processos
# - timeout 300s para conversões pesadas (LibreOffice, PDF)
# - max-requests 100 + jitter para evitar vazamento de memória a longo prazo
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 4 --timeout 300 --graceful-timeout 30 --max-requests 100 --max-requests-jitter 20 --log-level info app:app"]
