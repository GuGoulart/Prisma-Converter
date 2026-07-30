# Guia de Instalação e Execução Desktop — Windows, macOS e Linux

Este guia fornece instruções passo a passo detalhadas para instalar, configurar, executar, atualizar e desinstalar o **Prisma Converter** em ambiente Desktop.

---

## 🖥️ 1. Windows (10 / 11)

### Requisitos de Sistema
- **SO:** Windows 10 (64-bit) ou Windows 11.
- **Python:** Versão 3.10 ou superior.
- **Office:** Microsoft Office (Word/Excel/PowerPoint) instalado (opcional, para fidelidade máxima de conversões Word/Excel -> PDF via `pywin32`) ou LibreOffice.

### Passo a Passo de Instalação

1. **Instalar o Python:**
   - Faça o download no site oficial: [python.org/downloads](https://www.python.org/downloads/)
   - **IMPORTANTE:** Marque a opção **"Add Python to PATH"** durante o instalador.

2. **Obter o código do projeto:**
   ```powershell
   git clone https://github.com/GuGoulart/prisma-converter.git
   cd prisma-converter
   ```

3. **Criar e ativar ambiente virtual:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

4. **Instalar dependências:**
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Configurar variáveis de ambiente:**
   - Crie o arquivo `.env` na raiz do projeto com o conteúdo:
     ```env
     FLASK_ENV=development
     SECRET_KEY=sua_chave_secreta_aleatoria_aqui
     ```

6. **Executar a aplicação:**
   ```powershell
   python app.py
   ```
   - Abra o navegador em: `http://127.0.0.1:5000`

### Desinstalação no Windows
- Apague a pasta do projeto `prisma-converter` e o ambiente virtual `venv`.

---

## 🍎 2. macOS (Intel / Apple Silicon M1/M2/M3)

### Requisitos de Sistema
- **SO:** macOS 11.0 (Big Sur) ou superior.
- **Homebrew:** Gerenciador de pacotes instalado ([brew.sh](https://brew.sh)).

### Passo a Passo de Instalação

1. **Instalar dependências do sistema via Homebrew:**
   ```bash
   brew install python@3.10 libreoffice ffmpeg
   ```

2. **Clonar repositório:**
   ```bash
   git clone https://github.com/GuGoulart/prisma-converter.git
   cd prisma-converter
   ```

3. **Criar e ativar venv:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Instalar dependências Python:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Executar:**
   ```bash
   python app.py
   ```

---

## 🐧 3. Linux (Ubuntu / Debian / Fedora)

### Requisitos de Sistema
- **SO:** Ubuntu 20.04+, Debian 11+, Fedora 36+ ou Arch Linux.

### Passo a Passo no Ubuntu / Debian

1. **Instalar pacotes do sistema:**
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip libreoffice ffmpeg git
   ```

2. **Clonar e configurar:**
   ```bash
   git clone https://github.com/GuGoulart/prisma-converter.git
   cd prisma-converter
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Execução em Desenvolvimento:**
   ```bash
   python app.py
   ```

4. **Execução em Produção com Gunicorn:**
   ```bash
   gunicorn --workers 4 --bind 0.0.0.0:8080 app:app
   ```

---

## 🛠️ Solução de Problemas Desktop

- **Erro `ModuleNotFoundError`:** Certifique-se de que o ambiente virtual está ativo (`(venv)` visível no terminal).
- **Conversão de DOCX falhou no Linux:** Verifique se o LibreOffice foi instalado executando `soffice --version` no terminal.
- **Porta 5000 já em uso:** Altere a porta no final do arquivo `app.py` ou execute `flask run --port 5050`.
