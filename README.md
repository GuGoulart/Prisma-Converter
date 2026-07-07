# PRISMA

> Você pensa. O Prisma faz.
> De conversões a novas possibilidades. Tudo para seus arquivos, em um só lugar.

**Disponível Online:** [prisma-vmbr.onrender.com](https://prisma-vmbr.onrender.com/)

**Criador:** Gustavo Goulart Bretas — [github.com/GuGoulart](https://github.com/GuGoulart)

---

## O que é

O **Prisma Converter** é uma **Aplicação Web (SaaS)** desenhada para conversão universal de arquivos e manipulação avançada de PDFs diretamente no navegador. Focado em velocidade e segurança em nuvem, ele permite que usuários façam transformações complexas (como PDF para XLSX, ou juntar múltiplos PDFs) sem instalar absolutamente nada.

A ideia é simples: acesse o site, arraste um arquivo, escolha a ferramenta, clique no botão e baixe seu arquivo processado. Rápido, seguro e sem propagandas.

---

## Tecnologias utilizadas

| Camada | Tecnologia | Função |
|---|---|---|
| **Backend** | Python 3.10+ | Linguagem principal |
| **Framework web** | Flask | Servidor HTTP e sistema de rotas |
| **Conversor Universal**| `_via_pdf` (Hub) | Sistema inteligente de conversão cruzada para formatos incompatíveis nativamente |
| **Conversão Office** | pywin32 (`win32com`) | Word, Excel e PowerPoint → PDF (via MS Office local) |
| **Conversão LibreOffice**| subprocess + soffice | Word, Excel e PowerPoint → PDF (via LibreOffice) |
| **PDF → DOCX** | pdf2docx | Extração e conversão de PDFs para Word |
| **Extração de Tabelas**| pdfplumber | Extração avançada de dados tabulares do PDF para XLSX/CSV usando 3 estratégias de leitura |
| **Planilhas** | pandas + openpyxl | Leitura, edição e escrita eficiente de CSV e XLSX |
| **Imagens e PDFs** | PyMuPDF (`fitz`) / Pillow | Renderização, Mesclagem, Divisão, Proteção e Senhas em PDFs |
| **Segurança** | python-dotenv / secrets | Gerenciamento seguro de chaves de sessão e proteção contra CSRF (`.env`) |
| **Deploy** | Gunicorn | Servidor WSGI robusto para lidar com múltiplos workers em produção (Render) |
| **Frontend** | HTML + CSS + JS puro | Interface moderna, veloz e responsiva (sem frameworks) |
| **Tipografia** | Space Grotesk + Space Mono | Estética técnica/hacker via Google Fonts |

### Como foi feito

O backend é um servidor Flask com rotas organizadas para upload, geração de prévias em tempo real, conversões e ferramentas PDF. A inteligência principal mora no `converter.py`, atuando como uma verdadeira **fábrica de conversão universal**. Ele detecta de forma autônoma o motor disponível (Office da Microsoft ou LibreOffice) e utiliza um hub (`_via_pdf`) para encadear conversões complexas nos bastidores (exemplo: `PNG → PDF → DOCX`). Já as manipulações exclusivas de PDF (como dividir páginas, juntar arquivos, e trancar com senha) estão isoladas no `pdf_tools.py`.

O frontend é HTML/CSS/JS puro, sem a pesada cadeia de build do React ou dependências como Tailwind. O design foi concebido com uma forte estética sharp e técnica: dark mode elegante, bordas totalmente retas (0px radius), tipografia monospace para dados técnicos, grid de fundo paramétrico translúcido, menus modais com efeito de *glassmorphism* (`backdrop-filter`) e feedbacks interativos precisos com CSS animations.

---

## Fluxo da Aplicação

```text
Usuário envia arquivo (Conversão ou Ferramentas de PDF)
        ↓
Flask valida (magic bytes de segurança, extensão, CSRF Token via Cookie)
        ↓
Arquivo é salvo temporariamente por UUID isolado (uploads/<uuid>/)
        ↓
Interface carrega opções dinamicamente e gera a PRÉVIA do conteúdo
(Para planilhas, extrai dados via pandas; para DOCX, processa conversão de prévia em background)
        ↓
Usuário escolhe o destino ou ferramenta (juntar, dividir, senha)
        ↓
Flask aciona converter.py ou pdf_tools.py usando controle de Rate Limiting
        ↓
Arquivo finalizado é servido para download (stream direto)
        ↓
@after_this_request entra em ação + Cleanup Thread: todos os arquivos 
originais e resultantes são completamente incinerados do disco do servidor.
```

---

## Funcionalidades e Ferramentas

### 1. Conversor Universal Inteligente (52 Rotas)
Graças ao hub interno inteligente, arquivos transitam entre si utilizando processos intermediários invisíveis para o usuário. Isso possibilita combinações que normalmente não existem em sistemas de simples leitura:
- **CSV / XLSX** ↔ PDF, PNG, JPG, DOCX, PPTX
- **PDF** ↔ DOCX, PPT, PPTX, PNG, JPG, XLSX, CSV
- **DOCX / PPTX** ↔ PDF, PNG, JPG, XLSX, CSV

> **Nota Técnica:** Para evitar arquivos gerados corrompidos ou mal formatados, conversões de DOCX→PDF ou Planilhas para Imagens necessitam obrigatoriamente do MS Office ou LibreOffice rodando por trás do servidor. O sistema desabilita opções caso os motores não sejam detectados.

### 2. Ferramentas PDF Nativas
Além da conversão de formatos, o Prisma conta com ferramentas de manipulação direta via PyMuPDF:
- **Mesclar:** Suba quantos arquivos quiser e os junte em um PDF único.
- **Dividir:** Separe um PDF gigante em arquivos individuais compactados em um arquivo `.zip`.
- **Proteger:** Adicione uma camada de encriptação com senha de forma irreversível.
- **Desproteger:** Destranque um arquivo PDF permanentemente (é necessário informar a senha original).

---

## Instalação para Desenvolvedores (Ambiente Local)

Embora o Prisma seja focado para rodar em servidores Web/Cloud (SaaS), se você é um desenvolvedor e deseja rodar o projeto localmente para contribuir ou testar, siga os passos abaixo:

### Pré-requisitos
- **Python 3.10 ou superior**
- **Git** instalado na máquina
- **Microsoft Office** ou **LibreOffice** (Opcional, exigido apenas para formatar conversões de textos/slides no seu ambiente local).

### 1. Clone o repositório
```bash
git clone https://github.com/GuGoulart/prisma-converter.git
cd prisma-converter
```

### 2. Crie e ative o ambiente virtual
```bash
python -m venv venv
venv\Scripts\Activate.ps1   # No Windows (PowerShell)
```

### 3. Instale as dependências essenciais
O projeto conta com um script robusto de instalação via requirements:
```bash
pip install -r requirements.txt
```

### 4. Segurança Local (.env)
Para proteger a sessão e garantir o funcionamento correto dos formulários, crie um arquivo chamado `.env` (exatamente com esse nome) na pasta principal do projeto e adicione a seguinte linha com uma chave aleatória:
```text
SECRET_KEY=cole-aqui-uma-sequencia-maluca-de-letras-e-numeros
```

### 5. Execute o aplicativo
```bash
python app.py
```
O servidor será exposto localmente. Acesse `http://127.0.0.1:5000` no seu navegador!

---

## Deploy em Produção (Google Cloud Run)

Se você decidir publicar a aplicação na web de forma profissional:
O projeto já está 100% Dockerizado e otimizado para o **Google Cloud Run**.

Para garantir a segurança das sessões (`Token Inválido` ou expiração cruzada):
1. No console do Cloud Run, vá na aba **Variáveis de Ambiente e Segredos**.
2. Adicione a variável `SECRET_KEY` e defina um valor longo e aleatório.
*(Observação: Caso essa etapa seja esquecida, o aplicativo fará fallback automático para uma chave estática interna).*

---

## Features e Camadas de Segurança (Privacy First)

Sendo uma aplicação que lida com arquivos muitas vezes pessoais ou de trabalho de usuários, o nível de segurança do Prisma foi desenhado em camadas profundas:

- **Proteção Cross-Site (CSRF):** Sessões encriptadas através da Secret Key protegem contra submissão remota maliciosa de formulários.
- **Validação de Magic Bytes:** É inútil alguém tentar renomear um arquivo `.exe` ou vírus para `.pdf` e enviar. O sistema realiza varredura dos *headers* binários e bloqueia extensões falsificadas.
- **Bloqueio Hardcoded:** Arquivos suspeitos (`.bat`, `.sh`, `.py`, `.php`, `.vbs`) são rejeitados no ato.
- **Sanitização Universal:** O nome original de todo e qualquer arquivo submetido é formatado através do `secure_filename`, impedindo injeções de diretório em Linux/Windows.
- **Filtros Dinâmicos de Peso:** CSVs são barrados acima de 5MB (impedindo travamento via consumo desenfreado do Pandas na memória ram) enquanto PDFs possuem tolerância de 50MB.
- **Incineração Imediata:** Assim que a conversão finaliza, a função *decorator* `@after_this_request` varre os bytes do arquivo de entrada e de saída imediatamente. Em paralelo, a *thread* do `cleanup.py` desperta para expurgar pastas temporárias que os usuários tenham abandonado no meio da conversão.
- **Proteção Anti-Spam:** Sistema interno de Rate Limiting que rastreia IPs e Lock Mutex Threading que trava o backend em 3 processos simultâneos. Isso defende a memória do servidor caso dezenas de usuários cliquem em converter planilhas gigantes no mesmo segundo.

---

## Licença

**Todos os direitos reservados.** 
Este código, assets e design são de propriedade exclusiva de Gustavo Goulart Bretas. Não é permitida a cópia, bifurcação não-autorizada, distribuição, modificação ou uso comercial/monetizado desta base sem autorização prévia, formal e expressa do autor.

---

*Feito com atenção aos detalhes por [Gustavo Goulart Bretas](https://github.com/GuGoulart)*
