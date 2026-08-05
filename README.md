# PRISMA CONVERTER — Suíte Universal de Processamento de Arquivos & App Desktop / PWA

<div align="center">

![Prisma Logo Header](static/favicon.svg)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask Framework](https://img.shields.io/badge/framework-Flask-000000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Desktop Standalone](https://img.shields.io/badge/Desktop-PyInstaller%20%7C%20PyWebview-00c853.svg?style=for-the-badge&logo=windows&logoColor=white)](build_desktop.py)
[![PWA Ready](https://img.shields.io/badge/PWA-Enabled-success.svg?style=for-the-badge&logo=pwa&logoColor=white)](static/manifest.json)
[![Deploy Status](https://img.shields.io/badge/deploy-Google%20Cloud%20Run-brightgreen.svg?style=for-the-badge&logo=googlecloud&logoColor=white)](https://prisma-app.duckdns.org/)

**[ 🇧🇷 Português ](README.md) | [ 🇺🇸 English ](docs/README.en.md) | [ 🇪🇸 Español ](docs/README.es.md)**

*Você pensa. O Prisma faz. De conversões universais a manipulação avançada de arquivos, tudo em um só lugar.*

[Demonstração Online](https://prisma-app.duckdns.org/) • [Guia de Instalação Desktop](docs/installation/desktop.pt.md) • [Guia de Instalação Mobile PWA](docs/installation/mobile.pt.md)

</div>

---

## 📋 Sumário

- [Visão Geral](#-visão-geral)
- [Principais Funcionalidades](#-principais-funcionalidades)
- [Modos de Distribuição](#-modos-de-distribuição)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Arquitetura do Sistema](#-arquitetura-do-sistema)
- [Fluxo de Funcionamento da Aplicação](#-fluxo-de-funcionamento-da-aplicação)
- [Requisitos Mínimos e Pré-requisitos](#-requisitos-mínimos-e-pré-requisitos)
- [Instalação e Configuração Completa](#-instalação-e-configuração-completa)
- [Compilação do App Desktop Standalone (.exe)](#-compilação-do-app-desktop-standalone-exe)
- [Execução](#-execução)
- [Estrutura de Pastas](#-estrutura-de-pastas)
- [Explicação Detalhada dos Módulos](#-explicação-detalhada-dos-módulos)
- [Segurança e Privacidade em Camadas](#-segurança-e-privacidade-em-camadas)
- [Solução de Problemas Mais Comuns (FAQ)](#-solução-de-problemas-mais-comuns-faq)
- [Licença](#-licença)

---

## 🌟 Visão Geral

O **Prisma Converter** é uma **Aplicação Web (SaaS)**, **Progressive Web App (PWA)** e **Aplicativo Desktop Standalone Nativo (Windows `.exe`)** comercial desenvolvido para conversão universal de arquivos, manipulação avançada de documentos PDF, ferramentas de mídia e segurança cibernética.

Focado em **privacidade em primeiro lugar (Privacy-First)**, alta velocidade e facilidade de uso, o sistema realiza transformações complexas de arquivos (como PDF para XLSX com inteligência tabular, conversões cruzadas multi-formato, criptografia AES-256 e extração de paleta de cores) com processamento temporário totalmente isolado e **expurgo automático imediato** dos arquivos após o uso.

---

## 🚀 Principais Funcionalidades

### 1. 🔄 Conversor Universal Inteligente (52 Rotas Cruzadas)
Graças a um Hub de Conversão dinâmico (`_via_pdf`), arquivos transitam de maneira transparente entre formatos incompatíveis nativamente:
- **Documentos & Planilhas:** `PDF ↔ DOCX, XLSX, CSV, PPTX, PNG, JPG`
- **Apresentações:** `PPT, PPTX → PDF, DOCX, PNG, JPG`
- **Dados & Web:** `JSON ↔ CSV, XLSX, PDF`
- **Imagens Modernas:** `HEIC, WEBP, PNG, JPG → PDF, PNG, JPG`

### 2. 📄 Ferramentas Avançadas de PDF & Imagens
- **Mesclar PDFs:** Combinação ordenada de múltiplos documentos PDF em um único arquivo.
- **Dividir PDF:** Divisão por intervalo customizado, páginas individuais ou blocos fixos com saída compactada `.zip`.
- **Proteger / Desproteger PDF:** Adição e remoção de criptografia por senha via PyMuPDF (`fitz`).
- **Marca d'Água:** Inserção de texto d'água personalizado em PDFs.
- **Extração de Mídia:** Extração de imagens em alta resolução embutidas em PDFs.
- **Leitor de QR Code & Gerador:** Criação e leitura inteligente via AJAX.
- **Extrator de Paleta de Cores:** Análise K-Means de cores dominantes com códigos HEX e amostragem visual.

### 3. 🛡️ Segurança & Modificação de Arquivos
- **Criptografia AES-256:** Criptografia e descriptografia de arquivos genéricos.
- **Compressão ZIP / TAR.GZ:** Pacotes zipados com suporte a senha.
- **Verificação de Integridade Hash:** Cálculo instantâneo de checksum `MD5`, `SHA-1` e `SHA-256` com cópia em 1-clique.
- **Renomeador em Lote:** Padronização automatizada de nomes de arquivos.

---

## 💻 Modos de Distribuição

1. **💻 Computador / Desktop (`Prisma.exe`)**:
   - Compilado como executável standalone **`--onefile`** autônomo com ícone oficial da logo e servidor WSGI Waitress embutido.
   - Conversão 100% offline com **privacidade total**, salvando os arquivos gerados direto na pasta `Downloads` do usuário.
2. **📱 Celular / Mobile (PWA & APK)**:
   - Instalação via **PWA** com ícones adaptativos *maskable* (para Android e iOS) sem avisos do Play Protect.
   - Rota direta `/download-apk` para instalação via arquivo Android `.apk`.
3. **🌐 Nuvem / Web**:
   - Containerizado via Docker e rodando no **Google Cloud Run** (`https://prisma-app.duckdns.org`).

---

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologia | Função Principal |
|---|---|---|
| **Backend** | Python 3.10+ | Lógica de servidor e motores de conversão |
| **Framework Web** | Flask 3.1+ | Servidor HTTP, roteamento e gerenciamento de sessões |
| **Desktop Nativo** | PyWebview + Waitress + PyInstaller | Janela nativa GUI e servidor WSGI local para o `.exe` |
| **Engine de PDF** | PyMuPDF (`fitz`) / pdf2docx | Renderização, extração, mesclagem e criptografia |
| **Extração Tabular**| pdfplumber | Leitura de tabelas em PDFs estruturados para XLSX/CSV |
| **Processamento Dados**| pandas + openpyxl | Manipulação de planilhas CSV, XLSX e estruturas JSON |
| **Processamento Imagem**| Pillow (PIL) | Manipulação, conversão e geração de ícones maskable |
| **Segurança & Hash** | cryptography / hashlib | Criptografia AES-256 e geração de Hashes |
| **Frontend** | HTML5 / Vanilla CSS / JS | UI responsiva sem frameworks pesados, tema customizável |
| **PWA & Mobile** | Service Worker + Manifest v3 | Ícones adaptativos maskable e suporte PWA offline |
| **Produção & Deploy** | Gunicorn / Docker / Cloud Run | Container de alta performance hospedado no GCP |

---

## 📦 Instalação e Configuração Completa

### 1. Clonar o Repositório
```bash
git clone https://github.com/GuGoulart/Prisma-Converter.git
cd Prisma-Converter
```

### 2. Configurar o Ambiente Virtual

#### No Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### No Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependências
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔨 Compilação do App Desktop Standalone (.exe)

Para compilar o aplicativo executável nativo do Windows com o ícone oficial da logo do Prisma:

```bash
python build_desktop.py
```

O executável standalone será gerado automaticamente na pasta:
📁 **`dist/Prisma.exe`**

---

## 🚀 Execução

### Modo de Desenvolvimento
```bash
python app.py
```
Acesse a aplicação no navegador em: `http://127.0.0.1:5000`

### Modo App Desktop Nativo
Abra a pasta `dist/` e execute o **`Prisma.exe`**.

---

## 📂 Estrutura de Pastas

```text
Prisma-Converter/
├── core/                       # Módulos de negócios e motores de conversão
│   ├── __init__.py
│   ├── cleanup.py              # Thread e rotinas de expurgo automático de arquivos
│   ├── converter.py            # Fábrica principal de conversão universal (_via_pdf)
│   ├── file_tools.py           # Ferramentas de modificação (Hash, AES-256, ZIP)
│   ├── image_tools.py          # Extrator de paleta de cores e filtros PIL
│   ├── media_tools.py          # Utilitários de áudio/vídeo (MP4 -> MP3)
│   ├── pdf_tools.py            # Manipulação de PDF (PyMuPDF: merge, split, encrypt)
│   ├── qr_tools.py             # Leitor e gerador de QR Code
│   ├── security.py             # Magic Bytes, CSRF, Rate Limiting, Zip Bomb filter
│   └── storage.py              # Gerenciamento de diretórios temporários UUID
├── static/                     # Ativos estáticos, ícones e PWA
│   ├── css/
│   │   ├── animations.css      # Animações CSS e chaveadores de overlay
│   │   ├── components.css      # Estilização de botões, cards, modais e easter egg
│   │   ├── layout.css          # Grid principal, sidebar e navegação mobile
│   │   └── vars.css            # Variáveis do sistema de design e temas
│   ├── apple-touch-icon.png    # Ícone PWA para iOS (180x180)
│   ├── favicon.svg             # Logo SVG oficial com Delta neon (Δ)
│   ├── icon-192.png            # Ícone PWA 192x192
│   ├── icon-192-maskable.png   # Ícone adaptativo maskable para Android
│   ├── icon-512.png            # Ícone PWA 512x512
│   ├── icon-512-maskable.png   # Ícone adaptativo maskable para Android
│   ├── logo.ico                # Ícone do executável Windows (.exe)
│   ├── manifest.json           # Manifest PWA Web App v3 adaptativo
│   ├── script.js               # Script principal, seletor adaptativo e prévias
│   └── sw.js                   # Service Worker offline
├── templates/                  # Templates Jinja2 HTML5
│   ├── 404.html
│   ├── 500.html
│   ├── file_tools.html
│   ├── historico.html
│   ├── home.html
│   ├── index.html
│   └── pdf_tools.html
├── .dockerignore
├── .gitignore
├── Dockerfile                  # Containerização para Google Cloud Run
├── build_desktop.py            # Script de compilação automatizado PyInstaller --onefile
├── desktop_app.py              # Ponto de entrada do App Desktop Nativo (PyWebview + Waitress)
├── requirements.txt            # Lista de dependências Python
└── app.py                      # Ponto de entrada do servidor Flask
```

---

## 🛡️ Segurança e Privacidade em Camadas

- **Proteção CSRF:** Formulários protegidos com validação de tokens secretos por sessão.
- **Sanitização de Nomes (`secure_filename`):** Nomes de arquivos são completamente higienizados para prevenir ataques de *Path Traversal*.
- **Sem Logs de Dados de Usuário:** Conteúdos de arquivos processados jamais são salvos em logs.
- **Isolamento por UUID:** Cada sessão cria um diretório isolado usando UUID v4 aleatório (`uploads/<uuid>/`).
- **Expurgo Garantido:** Arquivos temporários são deletados imediatamente após o download via `@after_this_request` e limpos por rotina de faxina automatizada.

---

## 📄 Licença

**Todos os direitos reservados.**  
Este código, assets e design são de propriedade exclusiva de Gustavo Goulart Bretas. Para dúvidas sobre permissões ou uso corporativo, entre em contato através do perfil do GitHub: [github.com/GuGoulart](https://github.com/GuGoulart).

---

<div align="center">
  <i>Desenvolvido com excelência técnica por <a href="https://github.com/GuGoulart">Gustavo Goulart Bretas</a></i>
</div>
