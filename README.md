<div align="center">

# 💎 PRISMA CONVERTER

### **Aplicativo desktop local para converter, editar e proteger arquivos**

[![Português](https://img.shields.io/badge/Idioma-Portugu%C3%AAs-blue?style=for-the-badge)](README.md)
[![English](https://img.shields.io/badge/Language-English-red?style=for-the-badge)](README.en.md)
[![Español](https://img.shields.io/badge/Idioma-Espa%C3%B1ol-yellow?style=for-the-badge)](README.es.md)

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/Frontend-TypeScript-3178C6.svg?style=flat-square&logo=typescript&logoColor=white)](frontend/)
[![Licença: GPL v3](https://img.shields.io/badge/Licen%C3%A7a-GNU%20GPL%20v3-blue.svg?style=flat-square&logo=gnu)](LICENSE)

</div>

---

## Sobre

O Prisma roda no seu computador e abre em uma janela própria. Seus arquivos são processados localmente e não são enviados a servidores. As únicas conexões externas são as que você pede: baixar um vídeo por link e baixar o modelo de transcrição, uma única vez.

## Funcionalidades

| Área | Ferramentas |
|---|---|
| **Conversor** | PDF, DOCX, XLSX, CSV, JSON, PPT, PPTX, PNG, JPG, WEBP e HEIC, com prévia |
| **PDF** | Mesclar, dividir, proteger, desproteger, comprimir, marca d'água, extrair imagens, remover e girar páginas |
| **Áudio** | Converter, cortar, juntar, ajustar volume, normalizar, alterar velocidade, inverter e transcrever |
| **Vídeo** | Converter, comprimir, extrair MP3, gerar GIF, remover áudio, capturar quadro e baixar por link |
| **Arquivos** | ZIP e TAR.GZ, ZIP com senha, criptografia AES-256, hash, renomear em lote, mesclar planilhas |
| **Imagens** | Gerar e ler QR Code, extrair paleta de cores |

Toda tarefa mostra o progresso, pode ser cancelada e entra em uma fila, sem travar o resto do aplicativo. Os resultados ficam no histórico e são apagados pela política escolhida: 5 minutos, 15 minutos ou logo após o download.

### O que precisa de programas externos

O aplicativo detecta o que está instalado e mostra só as conversões possíveis.

| Recurso | Requisito |
|---|---|
| Áudio e vídeo | [FFmpeg](https://ffmpeg.org/download.html). Sem ele no PATH, o Prisma tenta baixar uma cópia automaticamente |
| DOCX, PPT e PPTX como origem; planilhas para PDF ou imagem | Microsoft Office **ou** [LibreOffice](https://www.libreoffice.org/download/) |
| Texto de imagens e PDFs digitalizados (OCR) | [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) |

## Início rápido no Windows

Requisito: [Python 3.11 ou superior](https://www.python.org/downloads/).

```bash
git clone https://github.com/GuGoulart/Prisma-Converter.git
```

Depois, dê dois cliques em `Prisma.bat` e escolha **[1] Iniciar**. Na primeira vez, ele instala as dependências em um ambiente próprio (`venv`) e cria um atalho na Área de Trabalho.

O servidor encerra sozinho alguns minutos depois que a última janela é fechada, desde que nenhuma tarefa esteja em andamento.

## Desenvolvimento

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
npm install

npm run watch         # recompila o frontend ao salvar
python app.py

python -m pytest tests   # testes do backend
npm run typecheck        # verificação de tipos
npm run e2e              # testes em navegador real
```

O frontend fica em `frontend/` e é compilado para `static/dist/`, que é versionado: **rodar o aplicativo não exige Node.js**. Rode `npm run build` antes de commitar alterações no frontend.

Para atualizar dependências, edite `requirements.in` e gere de novo o `requirements.txt` em um ambiente limpo.

## Arquitetura

```text
├── app.py                 # Inicialização, servidor e encerramento automático
├── core/
│   ├── jobs.py            # Fila de tarefas, progresso, cancelamento e autodestruição
│   ├── worker.py          # Executa tarefas pesadas em processo separado
│   ├── processo.py        # Subprocessos que podem ser cancelados e têm limite de tempo
│   ├── security.py        # Origem, CSRF, CSP e validação de entrada
│   ├── converter.py       # Conversor e detecção de Office, LibreOffice e OCR
│   └── ...                # PDF, áudio, vídeo, arquivos, QR Code e imagens
├── routes/
│   ├── pipeline.py        # Caminho único de toda ferramenta
│   └── ...                # Uma declaração por ferramenta
├── frontend/
│   ├── src/               # TypeScript: lib/ (base) e pages/ (uma por tela)
│   ├── css/               # Estilos compilados para static/dist
│   └── e2e/               # Testes de navegador (Playwright)
├── templates/             # Layout base, sidebar e páginas
├── static/                # Fontes, ícones e dist/ (compilado)
└── tests/                 # Testes do backend
```

## Privacidade e segurança

- **Processamento local:** o servidor escuta apenas em `127.0.0.1` e não usa recursos externos nas páginas.
- **Proteção contra outros sites:** valida `Host` e `Origin`, exige token CSRF e aplica uma política de segurança de conteúdo (CSP) sem scripts inline.
- **Isolamento:** downloads são feitos só por ID de tarefa. Nomes e parâmetros enviados nunca viram caminhos no disco.
- **Macros desabilitadas** ao abrir documentos pelo Office.
- **Exclusão:** os arquivos são apagados pelo sistema de arquivos. Isso não é uma destruição forense, que não pode ser garantida em SSDs.

## Licença

Distribuído sob a licença **GNU General Public License v3.0**. Veja [LICENSE](LICENSE).
