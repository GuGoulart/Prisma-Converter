<div align="center">

# 🌐 PRISMA CONVERTER

### **Suíte Universal de Processamento, Conversão e Segurança de Arquivos**

[![Português](https://img.shields.io/badge/Idioma-Portugu%C3%Aas-blue?style=for-the-badge)](README.md)
[![English](https://img.shields.io/badge/Language-English-red?style=for-the-badge)](README.en.md)
[![Español](https://img.shields.io/badge/Idioma-Espa%C3%B1ol-yellow?style=for-the-badge)](README.es.md)

<br/>

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask Framework](https://img.shields.io/badge/Framework-Flask-000000.svg?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7.svg?style=flat-square&logo=render&logoColor=white)](https://prisma-app.duckdns.org/)
[![Privacy First](https://img.shields.io/badge/Privacidade-100%25%20Seguro-success.svg?style=flat-square&logo=shield&logoColor=white)](#-privacidade--segurança)
[![License: GPL v3](https://img.shields.io/badge/Licen%C3%A7a-GNU%20GPL%20v3-blue.svg?style=flat-square&logo=gnu)](LICENSE)

[🚀 Demonstração Online](https://prisma-app.duckdns.org/) • [✨ Funcionalidades](#-funcionalidades) • [⚡ Início Rápido](#-início-rápido-no-windows) • [🏗️ Arquitetura](#%EF%B8%8F-arquitetura-do-projeto)


</div>

---

## 📖 Sobre o Projeto

O **Prisma Converter** é uma plataforma web completa para **conversão universal de arquivos**, **manipulação avançada de documentos PDF**, **criptografia AES-256** e **análise de integridade de dados**.

Projetado com foco total em **Privacidade em Primeiro Lugar (Privacy-First)** e alta performance, o sistema realiza transformações com isolamento de sessão via UUID v4 e expurgo automático de arquivos temporários.

---

## ✨ Funcionalidades

### 🔄 Conversor Universal de Arquivos
* **Documentos & Planilhas:** `PDF ↔ DOCX, XLSX, CSV, PPTX, PNG, JPG`
* **Apresentações:** `PPT, PPTX → PDF, DOCX, PNG, JPG`
* **Estruturas de Dados:** `JSON ↔ CSV, XLSX, PDF`
* **Imagens Modernas:** `HEIC, WEBP, PNG, JPG → PDF, PNG, JPG`

### 🛠️ Ferramentas Avançadas de PDF & Arquivos
| Categoria | Funcionalidades |
|---|---|
| 📄 **PDFs** | Mesclar, Dividir, Proteger/Desproteger com senha, Comprimir e Adicionar Marca d'Água |
| 🖼️ **Imagens** | Extração de mídia em lote de PDFs, Leitor/Gerador de QR Code e Extrator de Paleta de Cores |
| 🔒 **Segurança** | Criptografia AES-256-CBC, Geração de Hash (MD5, SHA1, SHA256) e ZIP com senha |
| 📁 **Utilitários** | Renomeação em lote automatizada e Mesclagem de planilhas Excel/CSV |

---

## ⚡ Início Rápido no Windows

### 1-Clique Automático (Modo Desktop)
1. Clone este repositório:
   ```bash
   git clone https://github.com/GuGoulart/Prisma-Converter.git
   cd Prisma-Converter
   ```
2. Dê **2 cliques no arquivo `Prisma.bat`**.
   > O sistema criará automaticamente o atalho na sua Área de Trabalho, iniciará o servidor e abrirá o navegador. Ao fechar o navegador, o servidor é encerrado sozinho em segundo plano!

### Execução via Terminal / Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate  # No Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Acesse no navegador: `http://127.0.0.1:5000`

---

## 🏗️ Arquitetura do Projeto

```text
Prisma-Converter/
├── app.py                      # Ponto de entrada modular da aplicação
├── routes/                     # Blueprints organizados por contexto
│   ├── views.py                # Rotas de páginas HTML e PWA
│   ├── converter.py            # Conversão universal de arquivos
│   ├── pdf.py                  # Ferramentas avançadas de PDF
│   ├── file_tools.py           # Compressão, Criptografia e Planilhas
│   ├── tools.py                # QR Code e Paleta de Cores
│   └── history.py              # Histórico de sessão e retenção
├── core/                       # Regras de negócio e motores
│   ├── utils.py                # Funções utilitárias centralizadas
│   ├── security.py             # Validação CSRF, Rate-limit e Magic Bytes
│   ├── converter.py            # Motores de conversão de arquivos
│   ├── pdf_tools.py            # Manipulação de PDFs via PyMuPDF
│   └── tasks.py                # Processamento assíncrono de tarefas
├── static/                     # CSS, JavaScript e assets visuais
├── templates/                  # Templates HTML5 responsivos
└── scripts/                    # Scripts de inicialização do sistema
```

---

## 🔒 Privacidade & Segurança

* 🗑️ **Expurgo Automático:** Arquivos temporários possuem ciclo de vida configurável (Instantâneo, 5 min ou 15 min) com exclusão definitiva.
* 🛡️ **Defesa em Profundidade:** Proteção contra Zip Bombs, validação de Magic Bytes e sanitize de nomes contra Path Traversal.

---

## 📜 Licença

Distribuído sob a licença **GNU General Public License v3.0 (GPLv3)**.
Esta licença garante que o código permaneça aberto e proíbe expressamente a venda comercial não autorizada por terceiros. Veja [LICENSE](LICENSE) para mais informações.

