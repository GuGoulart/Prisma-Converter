# Guia Completo de Instalação e Uso Mobile (PWA) — Android & iPhone (iOS)

O **Prisma Converter** foi desenvolvido como uma **Progressive Web App (PWA)** completa de nível comercial. Isso significa que você pode instalá-lo diretamente em seu smartphone Android ou iPhone sem precisar passar pela Google Play Store ou Apple App Store.

---

## 📱 1. Android (Google Chrome / Microsoft Edge / Samsung Internet)

### Vantagens no Android
- Experiência em tela cheia idêntica a um app nativo.
- Ícone na gaveta de aplicativos e tela inicial.
- Acesso rápido a ferramentas via Atalhos de Aplicativo (*App Shortcuts*).
- Cache offline para páginas e assets estáticos via Service Worker (`sw.js`).

### Passo a Passo de Instalação

1. **Acesse o site:**
   - Abra o navegador (Google Chrome recomendado) e acesse a URL da aplicação (ex: `https://prisma-vmbr.onrender.com`).

2. **Instalar via Prompt:**
   - Aguarde o banner de instalação surgir na parte inferior da tela e toque em **"Adicionar à Tela Inicial"** ou **"Instalar Aplicativo"**.

3. **Instalar via Menu Manual:**
   - Se o banner não aparecer, toque nos **três pontos (⋮)** no canto superior direito do Chrome.
   - Selecione **"Adicionar à tela inicial"** ou **"Instalar aplicativo"**.
   - Confirme a instalação no diálogo exibido.

4. **Uso & Atualização:**
   - O ícone do Prisma aparecerá na tela inicial e gaveta de apps.
   - As atualizações ocorrem automaticamente em segundo plano via Service Worker sempre que uma nova versão é publicada no servidor.

---

## 🍎 2. iPhone / iPad (iOS Safari)

### Especificidades e Limitações do iOS Safari
Devido às diretrizes do WebKit da Apple em dispositivos iOS:
- O prompt de instalação automática não é suportado no Safari. A adição deve ser feita manualmente pelo menu de compartilhamento.
- O modo *Standalone* roda em uma janela isolada com suporte a armazenamento local (`localStorage` e `CacheStorage`).

### Passo a Passo de Instalação no iOS

1. **Abra o Safari:**
   - Acesse a aplicação obrigatoriamente usando o **Safari** (outros navegadores no iOS como Chrome usam WebKit restrito).

2. **Abrir Menu de Compartilhamento:**
   - Toque no ícone de **Compartilhar** (quadrado com seta apontando para cima ⎋) na barra inferior do Safari.

3. **Adicionar à Tela de Início:**
   - Role a lista de opções para baixo e toque em **"Adicionar à Tela de Início"**.
   - Confirme o nome "Prisma" e toque em **"Adicionar"** no canto superior direito.

4. **Execução:**
   - Feche o Safari e toque no ícone do Prisma criado na Tela Inicial do seu iPhone. O aplicativo será aberto em modo tela cheia nativo sem barras de navegação do browser.

---

## 📋 Permissões Necessárias & Limitações Mobile

- **Permissões Exigidas:**
  - **Acesso a Arquivos / Armazenamento:** Exigido ao selecionar arquivos para conversão ou download.
  - **Câmera:** Opcional, para leitura direta de QR Codes via formulário web.
- **Limitações:**
  - Conversões pesadas de planilhas gigantes dependem da velocidade de conexão com a nuvem ou servidor local.
  - No iOS, o Service Worker pode ter seu cache expirado pelo sistema operacional caso o app fique sem uso por mais de 7 dias.
