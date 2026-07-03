# PRISMA

> Você pensa. O Prisma faz.
> De conversões a novas possibilidades. Tudo para seus arquivos, em um só lugar.

**Disponível Online:** [prisma-vmbr.onrender.com](https://prisma-vmbr.onrender.com/)

**Criador:** Gustavo Goulart Bretas — [github.com/GuGoulart](https://github.com/GuGoulart)

---

## O que é

O **Prisma Converter** é uma aplicação web local para conversão de arquivos entre diferentes formatos. Ele roda 100% na sua máquina — nenhum arquivo é enviado para nenhum servidor externo, nenhuma conta é necessária, e nenhum dado fica armazenado após o download.

A ideia é simples: arraste um arquivo, escolha o formato de destino, clique em converter, e baixe. Rápido, seguro e sem propaganda.

---

## Tecnologias utilizadas

| Camada | Tecnologia | Função |
|---|---|---|
| **Backend** | Python 3.10+ | Linguagem principal |
| **Framework web** | Flask | Servidor HTTP e rotas |
| **Conversor Universal**| `_via_pdf` (Hub) | Sistema de conversão cruzada para formatos incompatíveis nativamente |
| **Conversão Office** | pywin32 (`win32com`) | Word, Excel e PowerPoint → PDF (via MS Office) |
| **Conversão LibreOffice**| subprocess + soffice | Word, Excel e PowerPoint → PDF (via LibreOffice) |
| **PDF → DOCX** | pdf2docx | Extração e conversão de PDFs para Word |
| **PDF → Imagens** | PyMuPDF (`fitz`) | Renderização de páginas do PDF para PNG/JPG |
| **Imagem → PDF** | Pillow | Conversão de PNG/JPG para PDF |
| **Planilhas** | pandas + openpyxl | Leitura e escrita de CSV e XLSX |
| **Extração de Tabelas**| pdfplumber | Extração de dados tabulares de PDFs |
| **Encoding** | chardet *(opcional)* | Detecção automática de encoding em CSVs |
| **Frontend** | HTML + CSS + JS puro | Interface sem frameworks |
| **Tipografia** | Space Grotesk + Space Mono | Google Fonts |

### Como foi feito

O backend é um servidor Flask com rotas principais para upload, preview e conversão. Toda a lógica está isolada em `converter.py`, que atua como uma verdadeira **fábrica de conversão universal**. Ele detecta automaticamente o motor disponível (Microsoft Office ou LibreOffice) e utiliza um hub central (`_via_pdf`) para encadear conversões (ex: PNG → PDF → DOCX), permitindo que praticamente qualquer formato chegue a qualquer outro.

O frontend é HTML/CSS/JS puro — sem React, sem Tailwind, sem dependências de build. O design segue uma estética sharp/técnica: dark mode, sem bordas arredondadas (0px radius), tipografia monospace, grid de fundo translúcido, menus overlay com glassmorphism (backdrop-filter) e micro-animações dinâmicas.

---

## Como funciona

```text
Usuário envia arquivo
        ↓
Flask valida (magic bytes, extensão, tamanho, CSRF, rate limit)
        ↓
Arquivo salvo em pasta isolada por UUID (uploads/<uuid>/)
        ↓
Interface exibe opções de destinos cruzados dinamicamente
(Exibe prévias visuais em tempo real ou extração completa de dados para planilhas)
        ↓
Usuário escolhe formato de destino e clica em converter
        ↓
Flask aciona converter.py → Roteia via motor direto ou hub universal (_via_pdf)
        ↓
Arquivo convertido enviado via send_file (stream direto)
        ↓
@after_this_request apaga TODOS os arquivos imediatamente após o download
        ↓
Histórico da sessão atualizado + contador incrementado
```

### Detecção automática de motor

Na inicialização, o app tenta detectar qual motor de conversão está disponível:

1. **Microsoft Office** — via `win32com`. Requer Office instalado no Windows.
2. **LibreOffice** — via subprocess (`soffice --headless`). Detecta automaticamente nos caminhos padrão do Windows ou via PATH.
3. **Nenhum** — O app ainda funciona para conversões que não dependem de Office/LibreOffice (CSV↔XLSX, PDF→PNG, Imagem→PDF, PDF→DOCX).

---

## Formatos suportados (56 rotas de conversão)

Graças ao motor de hub universal embutido no Prisma, os arquivos podem transitar entre si utilizando passos intermediários inteligentes, permitindo **56 combinações** possíveis:

| Origem | Destinos Possíveis |
|---|---|
| **CSV** | XLSX, PDF, PNG, JPG, DOCX, PPTX |
| **XLSX** | CSV, PDF, PNG, JPG, DOCX, PPTX |
| **PDF** | DOCX, PPTX, PPT, PNG, JPG, XLSX, CSV |
| **DOCX** | PDF, PNG, JPG, XLSX, CSV, PPTX |
| **PPT / PPTX**| PDF, DOCX, XLSX, CSV, PNG, JPG, PPT/PPTX |
| **PNG / JPG** | PDF, JPG/PNG, DOCX, XLSX, CSV, PPTX |

> **Nota:** Conversões que exigem renderização visual complexa para PDF (DOCX→PDF, XLSX→PDF, PPT→PDF) necessitam do Microsoft Office ou LibreOffice instalados na máquina.

---

## Passo a passo — como usar

### Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python 3.10 ou superior** → [python.org/downloads](https://www.python.org/downloads/)
- **Git** → [git-scm.com](https://git-scm.com/)
- **Microsoft Office** (Word, Excel, PowerPoint) **ou** **LibreOffice** → [libreoffice.org](https://www.libreoffice.org/)

---

### 1. Clone o repositório

Abra o terminal (PowerShell ou CMD) e execute:

```bash
git clone https://github.com/GuGoulart/prisma-converter.git
cd prisma-converter
```

---

### 2. Crie e ative o ambiente virtual

```bash
# Cria o ambiente virtual
python -m venv venv

# Ativa no Windows (PowerShell)
venv\Scripts\Activate.ps1

# Ativa no Windows (CMD)
venv\Scripts\activate.bat
```

---

### 3. Instale as dependências

```bash
pip install flask
pip install pandas openpyxl
pip install pdf2docx
pip install pymupdf
pip install Pillow
pip install pywin32
pip install chardet
pip install pdfplumber
pip install python-pptx
```

Ou, use o `requirements.txt` do projeto:

```bash
pip install -r requirements.txt
```

---

### 4. Execute o aplicativo

```bash
python app.py
```

Você verá algo como:

```
[Prisma] Motor de conversão: office
 * Running on http://127.0.0.1:5000
```

---

### 5. Acesse no navegador

Abra o seu navegador e acesse: `http://localhost:5000`

---

## Funcionalidades de segurança

O Prisma Converter foi desenvolvido com segurança em camadas, mesmo sendo uma aplicação local:

- **Proteção CSRF:** Todos os formulários incluem um token único.
- **Validação de magic bytes:** O app verifica os headers binários dos arquivos para garantir que extensões não foram falsificadas.
- **Bloqueio de extensões duplas perigosas:** Bloqueia `.exe`, `.bat`, `.php`, `.py`, `.vbs`, etc.
- **Limite de tamanho inteligente:** Limites dinâmicos por tipo (ex: 5MB para CSV, 50MB para PDF).
- **Isolamento de sessão:** Pastas temporárias com UUIDs únicas.
- **Deleção imediata:** Arquivos são varridos do disco assim que o download termina, e uma thread em background limpa arquivos órfãos a cada 15 minutos.
- **Rate limiting e Pooling:** Máximo de 10 requisições por minuto por IP e travamento em 3 conversões simultâneas para evitar sobrecarga.

---

## Features que valem destaque

### Prévia de documentos e planilhas em tempo real
O sistema exibe o conteúdo visual do documento *antes* da conversão. Para planilhas (CSV e XLSX), todos os dados reais são extraídos sem limites de linhas e mostrados diretamente na tela com scroll nativo.

### Motor Universal de Conversão (`_via_pdf`)
O backend possui inteligência de roteamento. Se o usuário quiser converter um CSV para DOCX (dois formatos incompatíveis diretamente), o Prisma converte o CSV em um PDF temporário, e na sequência extrai e remonta o conteúdo como um arquivo de texto DOCX, de forma totalmente transparente e rápida.

### Detecção automática de encoding
CSVs do Windows muitas vezes vêm em `latin-1` ou `cp1252` em vez de `UTF-8`. O Prisma usa `chardet` para detectar o encoding correto antes de ler, evitando caracteres corrompidos.

### UI Responsiva e Glassmorphism
Design focado na experiência técnica: letreiros infinitos de status fixos no topo, menu lateral drawer no mobile com efeito backdrop-filter embaçando a tela traseira, e feedbacks interativos via CSS. 

### Atalhos de teclado
- `K`: Abre o seletor de arquivo
- `Enter`: Confirma a conversão
- `Esc`: Fecha o menu lateral no mobile

---

## Estrutura do projeto

```text
prisma-converter/
├── app.py              # Servidor Flask, rotas, segurança
├── converter.py        # Fábrica de conversões universais cruzadas
├── prisma.log          # Log de eventos
├── uploads/            # Pasta temporária (auto-limpante)
├── downloads/          # Pasta temporária (auto-limpante)
├── templates/
│   └── index.html      # UI Principal 
└── static/
    ├── style.css       # Estilos (Sharp, Dark Mode, animações)
    └── script.js       # Interatividade (Drag&drop, polling de cookie)
```

---

## Licença

**Todos os direitos reservados.** 
Este código e projeto são de propriedade exclusiva de Gustavo Goulart Bretas. Não é permitida a cópia, distribuição, modificação ou uso (comercial ou não) sem autorização prévia e expressa do autor.

---

*Feito com atenção aos detalhes por [Gustavo Goulart Bretas](https://github.com/GuGoulart)*
