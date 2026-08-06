# 🌐 PRISMA CONVERTER

<div align="center">

![Prisma Logo](static/favicon.svg)

### **Suíte Universal de Processamento, Conversão e Segurança de Arquivos**

*Você pensa. O Prisma faz. De conversões de documentos a utilitários avançados de segurança, tudo em uma única plataforma web moderna e ultrarrápida.*

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask Framework](https://img.shields.io/badge/Framework-Flask-000000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Google Cloud Run](https://img.shields.io/badge/Deploy-Cloud%20Run-4285F4.svg?style=for-the-badge&logo=googlecloud&logoColor=white)](https://prisma-app.duckdns.org/)
[![Privacy First](https://img.shields.io/badge/Privacy-100%25%20Local-success.svg?style=for-the-badge&logo=shield&logoColor=white)](#-segurança-e-privacidade-em-camadas)

[🚀 Demonstração Online](https://prisma-app.duckdns.org/) • [✨ Funcionalidades](#-funcionalidades-do-sistema) • [🛠️ Instalação Local](#%EF%B8%8F-instalação-e-execução-local)

</div>

---

## 📖 Sobre o Projeto

O **Prisma Converter** é uma plataforma web completa voltada para **conversão universal de arquivos**, **manipulação avançada de documentos PDF**, **criptografia de dados** e **análise de integridade de arquivos**.

Desenvolvido com foco total em **Privacidade em Primeiro Lugar (Privacy-First)** e alta velocidade, o Prisma realiza transformações complexas diretamente no servidor com isolamento temporário via UUID v4 e **expurgo automático imediato** de todos os arquivos após o processamento.

---

## ✨ Funcionalidades do Sistema

### 1. 🔄 Conversor Universal de Arquivos (50+ Rotas Cruzadas)
Conversões instantâneas com retenção de formatação e suporte a motor tabular inteligente:
- **Documentos & Planilhas:** `PDF ↔ DOCX, XLSX, CSV, PPTX, PNG, JPG`
- **Apresentações:** `PPT, PPTX → PDF, DOCX, PNG, JPG`
- **Estruturas de Dados:** `JSON ↔ CSV, XLSX, PDF`
- **Imagens Modernas:** `HEIC, WEBP, PNG, JPG → PDF, PNG, JPG`

### 2. ⚡ Ferramentas Avançadas (Tudo em Um Só Lugar)
- 📄 **Mesclar PDFs:** Unificação de múltiplos arquivos PDF em um único documento.
- ✂️ **Dividir PDF:** Separação por intervalos customizados ou páginas individuais em pacote ZIP.
- 🔒 **Proteger / Desproteger PDF:** Adição e remoção de criptografia de senhas em PDF.
- 💧 **Marca d'Água:** Inserção de marcas d'água de texto personalizadas em documentos.
- 🖼️ **Extração de Mídia:** Extração de todas as imagens internas de um PDF.
- 🔳 **QR Code (Gerador & Leitor):** Criação de QR Codes e decodificação instantânea por imagem.
- 🎨 **Extrator de Paleta de Cores:** Análise de cores dominantes com códigos HEX e amostragem visual.
- 📦 **Comprimir Arquivos (ZIP / TAR.GZ):** Agrupamento e compressão de múltiplos arquivos.
- 🔐 **ZIP com Senha:** Criação de arquivos ZIP protegidos com criptografia AES-256.
- 🛡️ **Criptografia AES-256-CBC:** Criptografe e descriptografe qualquer arquivo com segurança.
- 🔢 **Calculadora de Hash / Checksum:** Geração de assinaturas `MD5`, `SHA-1` e `SHA-256`.
- ✏️ **Renomear em Lote:** Padronização automatizada de nomeação de conjuntos de arquivos.

---

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologia | Função Principal |
|---|---|---|
| **Linguagem Principal** | Python 3.11+ | Execução do servidor e rotinas de conversão |
| **Framework Web** | Flask 3.1+ | Roteamento HTTP, sessões e APIs |
| **Motor de PDF** | PyMuPDF (`fitz`) | Renderização, mesclagem, divisão e criptografia de PDFs |
| **Inteligência Tabular**| pdfplumber | Extração precisa de tabelas em PDF para XLSX/CSV |
| **Manipulação de Dados**| pandas + openpyxl | Processamento de planilhas CSV, XLSX e JSON |
| **Imagens & Cores** | Pillow (PIL) | Processamento de imagens e análise de cores |
| **Segurança & Cifra** | cryptography / hashlib | Criptografia AES-256-CBC e hashes MD5/SHA256 |
| **Servidor HTTP & Deploy**| Gunicorn + Docker + Cloud Run | Servidor WSGI containerizado e hospedado no Google Cloud |

---

## 💻 Instalação e Execução Local

### 1. Clonar o Repositório
```bash
git clone https://github.com/GuGoulart/Prisma-Converter.git
cd Prisma-Converter
```

### 2. Criar e Ativar Ambiente Virtual

**No Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**No Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Iniciar a Aplicação
```bash
python app.py
```
Acesse no navegador em: `http://127.0.0.1:5000`

---

## 📂 Estrutura de Pastas

```text
Prisma-Converter/
├── core/                       # Módulos de regras de negócio
│   ├── cleanup.py              # Rotina automática de expurgo de arquivos
│   ├── converter.py            # Hub de conversão universal de formatos
│   ├── file_tools.py           # Ferramentas de Hash, AES-256 e ZIP
│   ├── image_tools.py          # Extrator de paleta de cores de imagem
│   ├── pdf_tools.py            # Manipulação avançada de PDF (PyMuPDF)
│   ├── qr_tools.py             # Leitor e gerador de QR Code
│   ├── security.py             # Validação de Magic Bytes, CSRF e Rate Limiting
│   └── storage.py              # Backend de armazenamento local / Cloud Storage
├── static/                     # Ativos visuais e scripts de interface
│   ├── favicon.svg             # Logotipo oficial em vetor SVG
│   ├── i18n.js                 # Sistema internacionalizador (PT, EN, ES)
│   ├── script.js               # Interações e manipuladores de UI
│   ├── style.css               # Estilização responsiva e temas
│   └── theme_customizer.js     # Personalizador dinâmico de cores e temas
├── templates/                  # Templates Jinja2 HTML5
│   ├── 404.html                # Página de erro 404 customizada
│   ├── 500.html                # Página de erro 500 customizada
│   ├── historico.html          # Histórico de arquivos da sessão
│   ├── home.html               # Página inicial com cards de navegação
│   ├── index.html              # Conversor de arquivos principal
│   └── pdf_tools.html          # Central de Ferramentas Avançadas
├── .github/workflows/          # Automação de CI/CD para Cloud Run
├── Dockerfile                  # Imagem Docker otimizada para o Cloud Run
├── requirements.txt            # Dependências Python do projeto
└── app.py                      # Ponto de entrada do aplicativo Flask
```

---

## 🔒 Segurança e Privacidade em Camadas

- **Proteção CSRF Integrada:** Validação de tokens de segurança em todas as requisições de formulário.
- **Isolamento por UUID v4:** Cada sessão gera diretórios totalmente isolados (`uploads/<uuid>/`).
- **Expurgo Automatizado:** Arquivos temporários são incinerados logo após o download (`@after_this_request`) e por tarefas em background.
- **Sanitização de Nomes:** Todos os nomes de arquivos enviados passam por `secure_filename()` para prevenir Path Traversal.

---

## 📄 Licença

**Todos os direitos reservados.**  
Propriedade de [Gustavo Goulart Bretas](https://github.com/GuGoulart).

---

<div align="center">

*Desenvolvido com excelência por <a href="https://github.com/GuGoulart">Gustavo Goulart Bretas</a>*

</div>
