# PRISMA CONVERTER — Suíte Universal de Processamento de Arquivos

<div align="center">

![Prisma Logo Header](static/favicon.svg)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask Framework](https://img.shields.io/badge/framework-Flask-000000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg?style=for-the-badge)](LICENSE)
[![PWA Ready](https://img.shields.io/badge/PWA-Enabled-success.svg?style=for-the-badge&logo=pwa&logoColor=white)](static/manifest.json)
[![Deploy Status](https://img.shields.io/badge/deploy-Render%20%7C%20Cloud%20Run-brightgreen.svg?style=for-the-badge&logo=googlecloud&logoColor=white)](https://prisma-vmbr.onrender.com/)

**[ 🇧🇷 Português ](README.md) | [ 🇺🇸 English ](docs/README.en.md) | [ 🇪🇸 Español ](docs/README.es.md)**

*Você pensa. O Prisma faz. De conversões universais a manipulação avançada de arquivos, tudo em um só lugar.*

[Demonstração Online](https://prisma-vmbr.onrender.com/) • [Guia de Instalação Desktop](docs/installation/desktop.pt.md) • [Guia de Instalação Mobile PWA](docs/installation/mobile.pt.md)

</div>

---

## 📋 Sumário

- [Visão Geral](#-visão-geral)
- [Principais Funcionalidades](#-principais-funcionalidades)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Arquitetura do Sistema](#-arquitetura-do-sistema)
- [Fluxo de Funcionamento da Aplicação](#-fluxo-de-funcionamento-da-aplicação)
- [Requisitos Mínimos e Pré-requisitos](#-requisitos-mínimos-e-pré-requisitos)
- [Instalação e Configuração Completa](#-instalação-e-configuração-completa)
  - [1. Clonar o Repositório](#1-clonar-o-repositório)
  - [2. Configurar o Ambiente Virtual](#2-configurar-o-ambiente-virtual)
  - [3. Instalar Dependências](#3-instalar-dependências)
  - [4. Configurar Variáveis de Ambiente](#4-configurar-variáveis-de-ambiente)
- [Execução](#-execução)
  - [Modo de Desenvolvimento](#modo-de-desenvolvimento)
  - [Modo de Produção](#modo-de-produção-gunicorn--docker)
- [Estrutura de Pastas](#-estrutura-de-pastas)
- [Explicação Detalhada dos Módulos](#-explicação-detalhada-dos-módulos)
- [Segurança e Privacidade em Camadas](#-segurança-e-privacidade-em-camadas)
- [Solução de Problemas Mais Comuns (FAQ)](#-solução-de-problemas-mais-comuns-faq)
- [Dicas de Uso e Boas Práticas](#-dicas-de-uso-e-boas-práticas)
- [Instruções para Atualização](#-instruções-para-atualização)
- [Contribuição](#-contribuição)
- [Licença](#-licença)

---

## 🌟 Visão Geral

O **Prisma Converter** é uma **Aplicação Web (SaaS) / Progressive Web App (PWA)** de nível comercial, desenvolvida para conversão universal de arquivos, manipulação avançada de documentos PDF, ferramentas de mídia e segurança cibernética diretamente no navegador.

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

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologia | Função Principal |
|---|---|---|
| **Backend** | Python 3.10+ | Lógica de servidor e motores de conversão |
| **Framework Web** | Flask 3.0+ | Servidor HTTP, roteamento e gerenciamento de sessões |
| **Engine de PDF** | PyMuPDF (`fitz`) / pdf2docx | Renderização, extração, mesclagem e criptografia |
| **Extração Tabular**| pdfplumber | Leitura de tabelas em PDFs estruturados para XLSX/CSV |
| **Processamento Dados**| pandas + openpyxl | Manipulação de planilhas CSV, XLSX e estruturas JSON |
| **Processamento Imagem**| Pillow (PIL) | Manipulação, conversão e extração de cores em imagens |
| **Automação Office** | pywin32 / LibreOffice CLI | Renderização de alta fidelidade para formatos MS Office |
| **Segurança & Hash** | cryptography / hashlib | Criptografia AES-256 e geração de Hashes |
| **Frontend** | HTML5 / Vanilla CSS / JS | UI responsiva sem frameworks pesados, dark/light mode |
| **PWA & Mobile** | Service Worker + Manifest v3 | Suporte PWA offline, atalhos mobile e instalação nativa |
| **Produção & Deploy** | Gunicorn / Docker | Servidor WSGI distribuído otimizado para nuvem |

---

## 🏗️ Arquitetura do Sistema

```
                  ┌────────────────────────────────────────┐
                  │          Cliente Web / Mobile          │
                  │   (HTML5 / Vanilla JS / PWA / Service) │
                  └───────────────────┬────────────────────┘
                                      │  HTTP POST / GET
                                      ▼
                  ┌────────────────────────────────────────┐
                  │            Servidor Flask              │
                  │ (Rotas, CSRF Validation, Rate Limit)   │
                  └───────────────────┬────────────────────┘
                                      │
          ┌───────────────────────────┴───────────────────────────┐
          ▼                                                       ▼
┌───────────────────┐                                   ┌───────────────────┐
│     core/         │                                   │     core/         │
│  converter.py     │                                   │   pdf_tools.py    │
│ (Hub _via_pdf,    │                                   │ (PyMuPDF, FitZ,   │
│  LibreOffice/Win) │                                   │  Merge, Split)    │
└─────────┬─────────┘                                   └─────────┬─────────┘
          │                                                       │
          └───────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │         Limpeza & Expurgo              │
                  │ (@after_this_request + core/cleanup.py)│
                  └────────────────────────────────────────┘
```

---

## 🔄 Fluxo de Funcionamento da Aplicação

```text
1. Envio de Arquivo
   └─► Validação de Extensão + Magic Bytes + Content-Type + Proteção Zip Bomb.
2. Isolamento em Disco
   └─► Arquivo salvo em diretório temporário único de 128-bit UUID (uploads/<uuid>/).
3. Geração de Prévia Dinâmica
   └─► Servidor gera prévia visual em tempo real (PDF/Imagem/HTML Data Table).
4. Execução do Engine (core/)
   └─► Processamento isolado pelo módulo responsável (conversão, mesclagem ou hash).
5. Download Seguro por Token
   └─► Arquivo finalizado servido via stream com cookie de acompanhamento de download.
6. Incineração Imediata
   └─► Garbage collector incinerador expurga arquivos originais e resultantes do disco.
```

---

## 💻 Requisitos Mínimos e Pré-requisitos

### Requisitos de Sistema
- **Sistema Operacional:** Windows 10/11, macOS 11+ (Intel/Apple Silicon) ou Linux (Ubuntu 20.04+, Debian 11+, Fedora 36+).
- **Processador:** Dual-core 2.0 GHz ou superior.
- **Memória RAM:** 2 GB mínimos (4 GB recomendados para conversões paralelas pesadas).
- **Espaço em Disco:** 500 MB de espaço livre.

### Pré-requisitos de Software
- **Python 3.10** ou superior instalado e adicionado ao `PATH`.
- **Git** para clonagem do repositório.
- **LibreOffice** (Opcional, porém recomendado em Linux/macOS para conversão nativa de DOCX/XLSX/PPTX para PDF).
- **Microsoft Office** (Opcional no Windows para máxima fidelidade via `pywin32`).

---

## 📦 Instalação e Configuração Completa

### 1. Clonar o Repositório
```bash
git clone https://github.com/GuGoulart/prisma-converter.git
cd prisma-converter
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

### 4. Configurar Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto (baseado em `.env.example`):

```env
FLASK_ENV=development
SECRET_KEY=sua_chave_secreta_super_segura_aqui_gerada_aleatoriamente
MAX_CONTENT_LENGTH=52428800
```

---

## 🚀 Execução

### Modo de Desenvolvimento
```bash
python app.py
```
Acesse a aplicação no navegador em: `http://127.0.0.1:5000`

### Modo de Produção (Gunicorn / Docker)

#### Com Gunicorn (Linux/macOS):
```bash
gunicorn --workers 4 --bind 0.0.0.0:8080 app:app
```

#### Com Docker:
```bash
docker build -t prisma-converter .
docker run -d -p 8080:8080 --name prisma-app prisma-converter
```

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
│   ├── storage.py              # Gerenciamento de diretórios temporários UUID
│   └── tasks.py                # Fila de tarefas assíncronas background
├── docs/                       # Documentação multilíngue e guias de instalação
│   ├── README.en.md            # Documentação em Inglês
│   ├── README.es.md            # Documentação em Espanhol
│   └── installation/           # Guias específicos por plataforma
│       ├── desktop.pt.md       # Instalação Desktop (Windows/macOS/Linux - PT)
│       ├── desktop.en.md       # Desktop Installation (EN)
│       ├── desktop.es.md       # Instalación Desktop (ES)
│       ├── mobile.pt.md        # Instalação Mobile PWA (Android/iOS - PT)
│       ├── mobile.en.md        # Mobile PWA Installation (EN)
│       └── mobile.es.md        # Instalación Mobile PWA (ES)
├── static/                     # Ativos estáticos e PWA
│   ├── css/
│   │   ├── animations.css      # Animações CSS e chaveadores de overlay
│   │   ├── components.css      # Estilização de botões, cards e formulários
│   │   ├── layout.css          # Grid principal, sidebar e navegação mobile
│   │   └── vars.css            # Variáveis do sistema de design e temas
│   ├── favicon.svg
│   ├── file_tools.js           # Lógica cliente para modificação de arquivos
│   ├── icon-192.png            # Ícone PWA 192x192
│   ├── icon-512.png            # Ícone PWA 512x512
│   ├── manifest.json           # Manifest PWA Web App v3
│   ├── pdf_tools.js            # Lógica cliente de ferramentas PDF
│   ├── script.js               # Script principal, alternador de tema e prévia
│   └── sw.js                   # Service Worker offline e cache v6
├── templates/                  # Templates Jinja2 HTML5
│   ├── 404.html
│   ├── 500.html
│   ├── file_tools.html
│   ├── home.html
│   ├── index.html
│   └── pdf_tools.html
├── .env.example                # Exemplo de configuração de variáveis de ambiente
├── .dockerignore
├── Dockerfile                  # Especificação para containerização de produção
├── requirements.txt            # Lista de dependências Python
└── app.py                      # Ponto de entrada do servidor Flask
```

---

## 🔍 Explicação Detalhada dos Módulos

### `core/converter.py`
Módulo central responsável pela conversão universal. Caso a conversão direta entre dois formatos não seja suportada nativamente por uma biblioteca Python, o sistema aciona o método `_via_pdf`, que encadeia a conversão em dois passos invisíveis (exemplo: `DOCX → PDF → PNG`).

### `core/security.py`
Blindagem de segurança em múltiplas camadas:
1. **Magic Bytes Check (`validar_magic`):** Varre a assinatura binária dos primeiros 16 bytes do arquivo enviado, impedindo executáveis disfarçados.
2. **Anti Zip-Bomb (`verificar_zip_bomb`):** Impede ataques de negação de serviço inspecionando a taxa de compressão e limite de descompactação (máximo de 100 MB).
3. **Rate Limiting (`rate_limit_required`):** Limita em 10 requisições por minuto por endereço IP.

### `static/css/vars.css` & `static/css/layout.css`
Engenharia do sistema de temas (Light Mode / Dark Mode) utilizando variáveis customizadas CSS. Garante suporte total a contraste, acessibilidade e corrigiu o comportamento de gaveta mobile no modo claro.

---

## 🛡️ Segurança e Privacidade em Camadas

- **Proteção CSRF:** Formulários protegidos com validação de tokens secretos por sessão.
- **Sanitização de Nomes (`secure_filename`):** Nomes de arquivos são completamente higienizados para prevenir ataques de *Path Traversal*.
- **Sem Logs de Dados de Usuário:** Conteúdos de arquivos processados jamais são salvos em logs ou compartilhados.
- **Isolamento por UUID:** Cada sessão cria um diretório isolado usando UUID v4 aleatório (`uploads/<uuid>/`).
- **Expurgo Garantido:** Arquivos temporários são deletados imediatamente após o download via `@after_this_request` e limpos periodicamente por thread de limpeza.

---

## ❓ Solução de Problemas Mais Comuns (FAQ)

<details>
<summary><b>1. Ocorreu erro ao converter arquivo DOCX ou PPTX para PDF no Linux.</b></summary>
<br>
<b>Causa:</b> O servidor Linux necessita do motor LibreOffice instalado para renderizar documentos de texto e apresentações.<br>
<b>Solução:</b> Execute <code>sudo apt install libreoffice</code> no Ubuntu/Debian ou consulte o <a href="docs/installation/desktop.pt.md">Guia de Instalação Desktop</a>.
</details>

<details>
<summary><b>2. Arquivo rejeitado com a mensagem "Assinatura de arquivo inválida".</b></summary>
<br>
<b>Causa:</b> A extensão do arquivo não condiz com seus <i>Magic Bytes</i> binários reais (ex: um arquivo executável renomeado para .pdf).<br>
<b>Solução:</b> Envie um arquivo válido no formato selecionado.
</details>

<details>
<summary><b>3. O menu hambúrguer no celular continuava escuro no modo claro.</b></summary>
<br>
<b>Solução:</b> Este problema foi corrigido na versão atual através das variáveis dinâmicas de tema <code>--mobile-nav-bg</code> e <code>--sidebar-mobile-bg</code>. Atualize seu repositório.
</details>

---

## 💡 Dicas de Uso e Boas Práticas

- **Atalhos de Teclado:** Na tela do conversor, pressione `K` para selecionar um arquivo e `Enter` para iniciar a conversão rapidamente.
- **Instalação PWA Mobile:** Adicione o aplicativo à Tela Inicial no Android ou iOS para ter acesso rápido estilo app nativo sem consumir armazenamento desnecessário.
- **Amostragem de Cores:** Ao extrair a paleta de cores de uma imagem, clique sobre qualquer código HEX exibido para copiá-lo diretamente para a área de transferência.

---

## 🔄 Instruções para Atualização

Para atualizar sua instalação local ou servidor para a versão mais recente:

```bash
git pull origin main
pip install -r requirements.txt --upgrade
python app.py
```

---

## 🤝 Contribuição

Contribuições são bem-vindas! Se você deseja sugerir melhorias ou corrigir um problema:

1. Faça um Fork do projeto.
2. Crie uma branch para sua funcionalidade (`git checkout -b feature/nova-funcionalidade`).
3. Commit suas alterações (`git commit -m 'Adiciona nova funcionalidade'`).
4. Envie para a branch (`git push origin feature/nova-funcionalidade`).
5. Abra um Pull Request.

---

## 📄 Licença

**Todos os direitos reservados.**  
Este código, assets e design são de propriedade exclusiva de Gustavo Goulart Bretas. Para dúvidas sobre permissões ou uso corporativo, entre em contato através do perfil do GitHub: [github.com/GuGoulart](https://github.com/GuGoulart).

---

<div align="center">
  <i>Desenvolvido com excelência técnica por <a href="https://github.com/GuGoulart">Gustavo Goulart Bretas</a></i>
</div>
