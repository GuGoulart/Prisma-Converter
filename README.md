<div align="center">

# 💎 PRISMA CONVERTER

### **Aplicativo Desktop Local • Suíte Completa de Conversão, Áudio, Vídeo, PDF e Ferramentas de Arquivos**

[![Português](https://img.shields.io/badge/Idioma-Portugu%C3%Aas-blue?style=for-the-badge)](README.md)
[![English](https://img.shields.io/badge/Language-English-red?style=for-the-badge)](README.en.md)
[![Español](https://img.shields.io/badge/Idioma-Espa%C3%B1ol-yellow?style=for-the-badge)](README.es.md)

<br/>

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask-000000.svg?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Plataforma](https://img.shields.io/badge/Plataforma-Windows%20Desktop-0078D6.svg?style=flat-square&logo=windows&logoColor=white)](#-início-rápido-no-windows)
[![100% Local & Privado](https://img.shields.io/badge/Privacidade-100%25%20Local-success.svg?style=flat-square&logo=shield&logoColor=white)](#-privacidade--segurança)
[![Licença: GPL v3](https://img.shields.io/badge/Licen%C3%A7a-GNU%20GPL%20v3-blue.svg?style=flat-square&logo=gnu)](LICENSE)

[✨ Funcionalidades](#-funcionalidades) • [⚡ Início Rápido](#-início-rápido-no-windows) • [🏗️ Arquitetura](#%EF%B8%8F-arquitetura-do-projeto) • [🔒 Privacidade & Segurança](#-privacidade--segurança)

</div>

---

## 📖 Sobre o Projeto

O **Prisma Converter** é um aplicativo desktop local e suíte universal para **conversão de arquivos**, **manipulação avançada de PDFs**, **edição e processamento de áudio e vídeo**, **download de mídia por link** e **criptografia de dados**.

Ao contrário de serviços online comuns, o Prisma opera de forma **100% local no seu computador**:
* 🛡️ **Privacidade Absoluta:** Seus arquivos nunca saem da sua máquina e não são enviados para servidores externos.
* ⚡ **Sem Limite de Upload:** Processamento local sem limites de tamanho de arquivo (`MAX_MB = 0`).
* 🪟 **Janela Nativa de Aplicativo:** Executa em modo janela independente (*App Mode*), sem abas ou barra de URL do navegador.

---

## ✨ Funcionalidades

### 🔄 Conversor Universal de Documentos
* **Documentos & Planilhas:** `PDF ↔ DOCX, XLSX, CSV, PPTX, PNG, JPG`
* **Apresentações:** `PPT, PPTX → PDF, DOCX, PNG, JPG`
* **Estruturas de Dados:** `JSON ↔ CSV, XLSX, PDF`
* **Imagens:** `HEIC, WEBP, PNG, JPG → PDF, PNG, JPG`

### 🎵 Ferramentas de Áudio
* **Conversão de Áudio:** `MP3, WAV, FLAC, AAC, OGG, M4A` com ajuste de bitrate e canais.
* **Corte & Aparo:** Definição de início e fim com precisão para extrair trechos.
* **Ajustes:** Normalização de volume e controle de qualidade.
* **Auto-configuração de FFmpeg:** Pronto para uso sem complicações de PATH (`static-ffmpeg`).

### 🎬 Ferramentas de Vídeo & Download
* **Conversão de Vídeo:** `MP4, MKV, AVI, MOV, WEBM` com controle de resolução e codecs.
* **Compressão de Vídeo:** Redução do tamanho mantendo alta fidelidade visual.
* **Corte & Extração:** Corte de trechos e extração da trilha sonora para MP3/WAV.
* **Download por Link:** Download de vídeos e áudios a partir de URLs da internet via `yt-dlp`.

### 🛠️ Ferramentas Avançadas de PDF & Utilitários
| Categoria | Funcionalidades |
|---|---|
| 📄 **PDFs** | Mesclar múltiplos PDFs, Dividir por páginas, Proteger/Desproteger com senha, Comprimir e Aplicar Marca d'Água |
| 🖼️ **Imagens** | Extração de mídia em lote de PDFs, Gerador/Leitor de QR Code e Extrator de Paleta de Cores |
| 🔒 **Segurança** | Criptografia AES-256-CBC, Hashes de verificação (MD5, SHA1, SHA256) e criação de ZIP protegido por senha |
| 📁 **Utilitários** | Renomeação inteligente em lote e Mesclagem de planilhas Excel/CSV |

### 🎨 Design Moderno & Personalização
* **Temas Customizáveis:** Modo Escuro e Modo Claro com **10 cores simétricas** em pares.
* **Sidebar Unificada:** Acesso direto a todas as 6 seções (Início, Conversor, Ferramentas Avançadas, Áudio, Vídeo e Histórico).
* **Internacionalização (i18n):** Suporte nativo completo a Português, Inglês e Espanhol.

---

## ⚡ Início Rápido no Windows

### 1-Clique com Atalho na Área de Trabalho (Recomendado)

1. Clone o repositório ou baixe os arquivos:
   ```bash
   git clone https://github.com/GuGoulart/Prisma-Converter.git
   cd Prisma-Converter
   ```

2. Instale as dependências uma única vez:
   ```bash
   pip install -r requirements.txt
   ```

3. Dê **dois cliques em `Prisma.bat`**:
   * O sistema criará automaticamente o atalho **"Prisma Converter"** na sua Área de Trabalho com o ícone personalizado.
   * O aplicativo iniciará em segundo plano e abrirá em uma janela nativa dedicada.
   * Se o app já estiver aberto e você clicar novamente no atalho, ele focará na janela existente sem conflito de portas.

### Central de Controle (`Prisma.bat`)

O arquivo `Prisma.bat` oferece um menu prático:
* `[1] Iniciar Prisma Converter`: Inicialização silenciosa da janela do aplicativo.
* `[2] Encerrar Servidor Local`: Libera a porta e encerra os processos em segundo plano.
* `[3] Criar/Atualizar Atalho`: Recria o atalho na sua Área de Trabalho.

### Execução Direta via Terminal
```bash
python app.py
```
O aplicativo abrirá diretamente em modo janela (`http://127.0.0.1:5000`).

---

## 🏗️ Arquitetura do Projeto

```text
Prisma-Converter/
├── app.py                      # Ponto de entrada do aplicativo local desktop
├── Prisma.bat                  # Central de controle e inicializador 1-clique
├── requirements.txt            # Dependências Python locais
├── core/                       # Motores de processamento e segurança
│   ├── converter.py            # Conversor universal de documentos e imagens
│   ├── pdf_tools.py            # Manipulação de PDFs via PyMuPDF
│   ├── audio_processor.py      # Processamento, conversão e corte de áudio
│   ├── video_processor.py      # Processamento e compressão de vídeo via FFmpeg
│   ├── video_downloader.py     # Motor de download por link via yt-dlp
│   ├── security.py             # Validação CSRF, sanitização e criptografia
│   ├── cleanup.py              # Expurgo automático de arquivos temporários
│   └── utils.py                # Utilitários de sistema e arquivos
├── routes/                     # Blueprints organizados por funcionalidade
│   ├── views.py                # Páginas principais (Home, Conversor, Avançadas)
│   ├── views_audio.py          # Páginas de Áudio e Vídeo
│   ├── converter.py            # Endpoints da API de conversão
│   ├── pdf.py                  # Endpoints da API de PDFs
│   ├── audio.py                # Endpoints da API de Áudio
│   ├── video.py                # Endpoints da API de Vídeo e Download
│   ├── file_tools.py           # Compressão, Criptografia e Planilhas
│   ├── tools.py                # QR Code e Paleta de Cores
│   └── history.py              # Histórico local da sessão
├── static/                     # CSS, JavaScript e assets visuais
│   ├── css/                    # Estilos modulares (vars, layout, components)
│   ├── audio/                  # Assets e scripts dedicados de áudio e vídeo
│   ├── theme_customizer.js     # Customizador de temas e cores (10 pares)
│   ├── i18n.js                 # Dicionário de traduções (PT / EN / ES)
│   └── logo.ico                # Ícone do aplicativo desktop
├── templates/                  # Telas HTML responsivas e modais
└── scripts/                    # Scripts de automação desktop
    ├── Iniciar_Prisma.vbs      # Inicializador silencioso (sem tela preta do cmd)
    └── criar_atalho.ps1        # Gerador do atalho na Área de Trabalho
```

---

## 🔒 Privacidade & Segurança

* 💻 **Processamento 100% Local:** Nada é enviado para a nuvem; os dados nunca trafegam pela internet pública.
* 🗑️ **Limpeza Automática:** Ciclo de vida de arquivos temporários com exclusão segura e expurgo automático na inicialização.
* 🛡️ **Proteção Robusta:** Sanitização rigorosa de nomes de arquivos contra *Path Traversal*, proteção contra *Zip Bombs* e validação de cabeçalhos MIME.

---

## 📜 Licença

Distribuído sob a licença **GNU General Public License v3.0 (GPLv3)**.  
Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
