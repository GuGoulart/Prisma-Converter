# PRISMA Converter

> Conversor de arquivos local, seguro e sem frescura. Feito com Flask + Python.

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
| **Conversão Office** | pywin32 (`win32com`) | Word, Excel e PowerPoint → PDF (via MS Office) |
| **Conversão LibreOffice** | subprocess + soffice | Word, Excel e PowerPoint → PDF (via LibreOffice) |
| **PDF → DOCX** | pdf2docx | Extração e conversão de PDFs |
| **PDF → PNG** | PyMuPDF (`fitz`) | Renderização de páginas do PDF |
| **Imagem → PDF** | Pillow | Conversão de PNG/JPG para PDF |
| **Planilhas** | pandas + openpyxl | Leitura e escrita de CSV e XLSX |
| **Encoding** | chardet *(opcional)* | Detecção automática de encoding em CSVs |
| **Frontend** | HTML + CSS + JS puro | Interface sem frameworks |
| **Tipografia** | Space Grotesk + Space Mono | Google Fonts |

### Como foi feito

O backend é um servidor Flask com duas rotas principais: `/upload` (recebe o arquivo, valida, e exibe as opções de conversão) e `/converter` (executa a conversão e devolve o arquivo via `send_file`). Toda a lógica de conversão está isolada em `converter.py`, que detecta automaticamente na inicialização qual motor está disponível (Microsoft Office ou LibreOffice) e usa o mais adequado para cada tarefa.

O frontend é HTML/CSS/JS puro — sem React, sem Tailwind, sem dependências de build. O design segue uma estética sharp/técnica: dark mode, sem bordas arredondadas, tipografia monospace, grid de fundo, e micro-animações via CSS puro.

---

## Como funciona

```
Usuário envia arquivo
        ↓
Flask valida (magic bytes, extensão, tamanho, CSRF, rate limit)
        ↓
Arquivo salvo em pasta isolada por UUID (uploads/<uuid>/)
        ↓
Interface exibe opções de conversão disponíveis
(CSV e XLSX também mostram prévia das 5 primeiras linhas)
        ↓
Usuário escolhe formato de destino e clica em converter
        ↓
Flask aciona converter.py → motor correto (Office ou LibreOffice)
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
3. **Nenhum** — O app ainda funciona para conversões que não dependem de Office/LibreOffice (CSV↔XLSX, PDF→PNG, Imagem→PDF).

---

## Formatos suportados

| Entrada | Saída |
|---|---|
| CSV | XLSX, PDF |
| XLSX | CSV, PDF |
| PDF | DOCX, PNG |
| DOCX | PDF |
| PPT | PDF |
| PPTX | PDF |
| PNG | PDF |
| JPG / JPEG | PDF |

> **Nota:** Conversões para PDF que envolvam Office (DOCX, XLSX, PPT, PPTX) requerem Microsoft Office ou LibreOffice instalado.

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

> Você saberá que está ativo quando aparecer `(venv)` no início da linha do terminal.

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
```

Ou, se quiser use o `requirements.txt` do projeto:

```bash
pip install -r requirements.txt
```

---

### 4. (Opcional) Verifique se o LibreOffice está no PATH

Se você usa LibreOffice em vez do Microsoft Office, o app o detecta automaticamente nos caminhos padrão. Para verificar:

```bash
soffice --version
```

Se retornar algo como `LibreOffice 7.x.x`, está funcionando. Se não, adicione o caminho manualmente ao PATH do Windows ou edite a lista `_caminhos` em `converter.py`.

---

### 5. Execute o aplicativo

```bash
python app.py
```

Você verá algo como:

```
[Prisma] Motor de conversão: office
 * Running on http://127.0.0.1:5000
```

---

### 6. Acesse no navegador

Abra o seu navegador e acesse:

```
http://localhost:5000
```

---

### 7. Use o conversor

1. **Arraste** um arquivo para a área de upload, ou clique para selecionar
2. Clique em **Enviar**
3. Se for CSV ou XLSX, uma **prévia das 5 primeiras linhas** aparecerá à direita
4. Selecione o **formato de destino** nos cards de opção
5. Clique em **Converter e baixar**
6. O download começa automaticamente — os arquivos são apagados do servidor logo após

---

### 8. Atalhos de teclado

| Tecla | Ação |
|---|---|
| `K` | Abre o seletor de arquivo |
| `Enter` | Confirma a conversão (equivale a clicar no botão) |
| `Esc` | Fecha o menu lateral no mobile |

---

### 9. Encerrando o app

No terminal, pressione `Ctrl + C` para parar o servidor.

Para desativar o ambiente virtual:

```bash
deactivate
```

---

## Funcionalidades de segurança

O Prisma Converter foi desenvolvido com segurança em camadas, mesmo sendo uma aplicação local.

### Proteção CSRF
Todos os formulários incluem um token CSRF gerado via `secrets.token_hex(32)` e armazenado na sessão Flask. Qualquer requisição POST sem o token correto é rejeitada imediatamente.

### Validação de magic bytes
O app não confia apenas na extensão do arquivo. Ele lê os primeiros bytes do arquivo e verifica se batem com o formato declarado:
- PDF: `%PDF`
- DOCX / XLSX / PPTX: `PK\x03\x04` (cabeçalho ZIP do Office Open XML)
- PPT / XLS / DOC antigos: `\xd0\xcf\x11\xe0` (cabeçalho OLE2)
- PNG: `\x89PNG`
- JPG: `\xff\xd8\xff`

Se não bater, o arquivo é rejeitado e apagado.

### Bloqueio de extensões duplas perigosas
Arquivos com extensões intermediárias perigosas (ex: `documento.pdf.exe`, `planilha.xlsx.bat`) são bloqueados antes mesmo de serem salvos. A lista de extensões bloqueadas inclui: `exe`, `bat`, `cmd`, `php`, `sh`, `ps1`, `vbs`, `js`, `jar`, `py`, `dll`, entre outras.

### Limite de tamanho por tipo de arquivo
Cada formato tem um limite próprio, mais inteligente do que um limite global:

| Formato | Limite |
|---|---|
| CSV | 5 MB |
| DOCX / XLSX | 20 MB |
| PNG / JPG | 10 MB |
| PDF / PPT / PPTX | 50 MB |

### Isolamento por pasta de sessão
Cada upload cria uma subpasta única (`uploads/<uuid>/`) exclusiva para aquela sessão. Não há risco de colisão entre arquivos de diferentes usuários.

### Token de sessão por arquivo
Após o upload, o servidor salva um token na sessão Flask vinculado à pasta do arquivo. Na conversão, valida que o arquivo pertence à sessão atual. Isso impede que uma URL manipulada acesse arquivos de outro usuário.

### Deleção imediata após download
Usando o decorator `@after_this_request` do Flask, todos os arquivos (upload e saída) são apagados do disco imediatamente após o `send_file` ser concluído. Em caso de erro na conversão, os arquivos de upload também são apagados.

### Rate limiting por IP
Máximo de **10 ações por minuto por IP**, implementado sem biblioteca externa. Protege contra abuso e loops automáticos.

### Limite de conversões paralelas
O servidor processa no máximo **3 conversões simultâneas**. Requisições excedentes recebem uma mensagem de "servidor ocupado" em vez de travar o processo.

### Timeout de conversão
Cada conversão tem um timeout de **120 segundos**, implementado via `threading.Event`. Se o processo travar (ex: arquivo corrompido, Office travado), ele é interrompido e o usuário recebe uma mensagem de erro clara.

### Cabeçalhos HTTP de segurança
Todas as respostas incluem cabeçalhos de segurança HTTP aplicados via `@app.after_request`:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: no-referrer
```

### Limpeza residual em background
Uma thread em daemon roda a cada 15 minutos e remove qualquer arquivo com mais de 15 minutos que, por algum motivo, não tenha sido apagado (ex: sessão abandonada, queda de conexão).

### Logging estruturado
Todas as ações relevantes (uploads, conversões, erros, tentativas bloqueadas por rate limit ou CSRF) são registradas em `prisma.log` com timestamp, nível e IP de origem.

---

## Features que valem destaque

### Detecção automática de encoding e separador em CSVs
CSVs do Windows muitas vezes vêm em `latin-1` ou `cp1252` em vez de `UTF-8`. O Prisma usa `chardet` (se instalado) para detectar o encoding correto antes de ler. Além disso, usa `sep=None, engine="python"` do pandas para detectar automaticamente se o separador é `,`, `;`, `|` ou `Tab` — sem configuração manual.

### Prévia de tabela em tempo real
Para arquivos CSV e XLSX, o app exibe uma prévia das 5 primeiras linhas e até 8 colunas assim que o arquivo é enviado, antes mesmo de converter. Útil para confirmar que o arquivo correto foi selecionado.

### Histórico da sessão
As últimas 5 conversões da sessão aparecem com formato de origem, destino, nome do arquivo e horário. Os dados ficam apenas na sessão Flask (memória do servidor) e somem quando o servidor é reiniciado.

### Contador de conversões ao vivo
A sidebar exibe o total de conversões realizadas desde que o servidor foi iniciado.

### Motor visível na sidebar
A sidebar indica qual motor está sendo usado (`MS Office` ou `LibreOffice`), para que o usuário saiba exatamente o que está acontecendo.

### Design totalmente responsivo com drawer mobile
No mobile, a sidebar vira um drawer deslizante acessível pelo ícone de menu. Os botões têm 56px de altura para conforto no toque.

### Sem dependências de build no frontend
O frontend usa HTML, CSS e JS puros. Não há npm, webpack, Vite ou qualquer ferramenta de build. Para editar o visual, basta alterar os arquivos estáticos diretamente.

---

## Estrutura do projeto

```
prisma-converter/
├── app.py              # Servidor Flask, rotas, segurança
├── converter.py        # Lógica de conversão, detecção de motor
├── prisma.log          # Log de eventos (gerado automaticamente)
├── uploads/            # Pasta temporária de uploads (auto-criada)
├── downloads/          # Pasta temporária de saídas (auto-criada)
├── templates/
│   └── index.html      # Interface principal
└── static/
    ├── style.css        # Estilos (dark, sharp, sem border-radius)
    └── script.js        # Interatividade, drawer, cookie polling
```

---

## Licença

MIT — use, modifique e distribua à vontade. Créditos são bem-vindos mas não obrigatórios.

---

*Feito com atenção aos detalhes por [Gustavo Goulart Bretas](https://github.com/GuGoulart)*
