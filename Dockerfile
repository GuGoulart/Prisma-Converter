FROM python:3.11-bookworm-slim

# Instala LibreOffice (headless), Tesseract OCR e dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
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

# ── Porta ────────────────────────────────────────────────────────────────────
# O Cloud Run injeta PORT dinamicamente (padrão 8080)
ENV PORT=8080
EXPOSE 8080

# ── Variáveis obrigatórias ────────────────────────────────────────────────────
# SECRET_KEY deve ser definida via Cloud Run Secret Manager ou variável de ambiente.
# Nunca deixar vazia em produção.
# ENV SECRET_KEY=<definir-via-cloud-run-secrets>

# ── Prevenção de deadlocks (libs C++ multi-thread: OpenCV, NumPy) ─────────────
ENV OMP_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV VECLIB_MAXIMUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1

# ── Fase 3: Variáveis opcionais para escala horizontal ───────────────────────
#
# REDIS_URL
#   Quando definido, habilita:
#     - Rate limiting distribuído via Flask-Limiter + Redis
#     - Fila de tarefas assíncronas via Celery
#   Formato: redis://:senha@host:6379/0
#   Sem esta variável: modo in-memory (funcional para instância única)
# ENV REDIS_URL=redis://redis-host:6379/0
#
# GCS_BUCKET
#   Quando definido, habilita armazenamento de arquivos no Google Cloud Storage.
#   Requer que a Service Account do Cloud Run tenha papel "Storage Object Admin".
#   Sem esta variável: armazenamento local em disco (efêmero no Cloud Run).
# ENV GCS_BUCKET=meu-bucket-prisma-prod
# ENV GCS_PREFIX=prisma/
#
# MAX_PARALELAS
#   Número máximo de conversões simultâneas (padrão: 4)
# ENV MAX_PARALELAS=4

# ── Worker ───────────────────────────────────────────────────────────────────
# --workers 1: Sem múltiplos workers para evitar deadlocks com OpenCV/LibreOffice.
# --timeout 120: Conversões pesadas podem demorar até 120s.
# Para escala horizontal, adicionar REDIS_URL e AUMENTAR o --timeout para 180.
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app:app
