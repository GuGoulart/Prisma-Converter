FROM python:3.11-slim

# Instala LibreOffice (headless) e dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    fonts-dejavu \
    fonts-liberation \
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

# Render/Railway definem a variável PORT automaticamente
ENV PORT=8080
EXPOSE 8080

# Roda com gunicorn (produção) em vez do servidor de dev do Flask
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 app:app
