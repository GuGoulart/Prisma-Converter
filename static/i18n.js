/**
 * i18n.js — Sistema Completo de Internacionalização (Português, Inglês, Espanhol)
 * Prisma Converter — Suíte Universal de Arquivos
 */

const translations = {
    pt: {
        // --- Navegação & Sidebar ---
        "nav.home": "Início",
        "nav.converter": "Conversor de arquivos",
        "nav.advanced": "Ferramentas Avançadas",
        "nav.modify": "Modificar Arquivos",
        "sidebar.menu": "Menu",
        "sidebar.limit": "Limite",
        "sidebar.conversions": "Conversões",
        "sidebar.theme": "Tema",
        "sidebar.language": "Idioma",

        // --- Home Page ---
        "home.title": "Você pensa<br><em>O Prisma faz</em>",
        "home.subtitle": "De conversões a novas possibilidades. Tudo para seus arquivos, em um só lugar.",
        "home.card1.title": "Conversor de Arquivos",
        "home.card1.desc": "Converta documentos (PDF, DOCX, XLSX, PPTX, CSV), imagens (PNG, JPG, WEBP, HEIC) e arquivos de dados JSON com agilidade.",
        "home.card1.btn": "Acessar Conversor",
        "home.card2.title": "Ferramentas Avançadas",
        "home.card2.desc": "Gere e leia QR Codes personalizados, extraia a paleta de cores dominantes de imagens e converta vídeos MP4 em áudio MP3.",
        "home.card2.btn": "Acessar Ferramentas",
        "home.card3.title": "Modificar Arquivos",
        "home.card3.desc": "Comprima pacotes em ZIP / TAR.GZ, proteja arquivos com senha, criptografe com AES-256, calcule Hash e renomeie em lote.",
        "home.card3.btn": "Acessar Modificador",
        "home.feat1.title": "Privacidade Garantida",
        "home.feat1.desc": "Processamento seguro e local. Seus arquivos não são armazenados permanentemente nem compartilhados com terceiros.",
        "home.feat2.title": "Sem Necessidade de Conta",
        "home.feat2.desc": "Acesso imediato e gratuito a todas as funcionalidades. Sem cadastros, sem formulários e sem complicação.",
        "home.feat3.title": "Ecossistema Unificado",
        "home.feat3.desc": "Tudo o que você precisa para conversão, manipulação, segurança e análise de arquivos em uma única interface moderna.",

        // --- Conversor (index.html) ---
        "conv.header.title": "Conversor de <em>Arquivos</em>",
        "conv.header.sub": "Converta documentos, imagens e dados multiformato de maneira rápida, direta e 100% local.",
        "conv.step1.label": "Selecione o arquivo",
        "conv.upload.drag": "Arraste o arquivo aqui",
        "conv.upload.btn": "Enviar",
        "conv.step2.label": "Escolha o destino",
        "conv.ori.title": "ORIENTAÇÃO DO PDF",
        "conv.ori.portrait": "Retrato",
        "conv.ori.landscape": "Paisagem",
        "conv.btn.convert": "Converter e baixar",
        "conv.btn.another": "Converter outro arquivo",
        "conv.history.title": "Histórico da sessão",
        "conv.history.unit": "conversão(ões)",
        "conv.preview.label": "Visualização",
        "conv.preview.empty": "Nenhum arquivo enviado",
        "conv.preview.emptySub": "A prévia aparece aqui.<br>Clique em um formato para ver como ficará.",

        // --- Ferramentas Avançadas (pdf_tools.html) ---
        "pdf.header.title": "Ferramentas <em>Avançadas</em>",
        "pdf.header.sub": "Utilitários poderosos para processamento rápido e local de documentos e imagens.",
        "pdf.sec.pdf": "Ferramentas PDF",
        "pdf.merge.title": "Mesclar PDFs",
        "pdf.merge.desc": "Selecione vários arquivos PDF e junte-os em um único documento contínuo. Você pode clicar várias vezes para ir adicionando mais arquivos.",
        "pdf.merge.choose": "Escolher Arquivos",
        "pdf.merge.action": "Mesclar e baixar",
        "pdf.split.title": "Dividir PDF",
        "pdf.split.desc": "Separe cada página de um PDF em arquivos independentes (entregues em ZIP).",
        "pdf.split.choose": "Escolher Arquivo",
        "pdf.split.opt.ind": "Página por página",
        "pdf.split.opt.fix": "A cada N páginas",
        "pdf.split.opt.cust": "Páginas específicas",
        "pdf.split.action": "Dividir e baixar ZIP",
        "pdf.protect.title": "Proteger PDF",
        "pdf.protect.desc": "Adicione uma senha forte para criptografar e restringir a abertura do PDF.",
        "pdf.protect.ph": "Senha desejada",
        "pdf.protect.action": "Proteger e baixar",
        "pdf.unprotect.title": "Desproteger PDF",
        "pdf.unprotect.desc": "Remova a senha de um PDF criptografado (necessita da senha original).",
        "pdf.unprotect.ph": "Senha do PDF",
        "pdf.unprotect.action": "Desproteger e baixar",
        "pdf.compress.title": "Comprimir PDF",
        "pdf.compress.desc": "Reduza o tamanho do seu PDF otimizando imagens internas.",
        "pdf.compress.action": "Comprimir e baixar",
        "pdf.wm.title": "Marca D'água PDF",
        "pdf.wm.desc": "Adicione uma marca d'água em texto em todas as páginas do seu PDF.",
        "pdf.wm.ph": "Texto da Marca D'água",
        "pdf.wm.action": "Aplicar e baixar",
        "pdf.extract.title": "Extrair Imagens PDF",
        "pdf.extract.desc": "Extraia todas as imagens embutidas em um PDF. Retorna um arquivo ZIP.",
        "pdf.extract.action": "Extrair e baixar ZIP",
        "pdf.sec.media": "Imagens e Mídia",
        "pdf.qrgen.title": "Gerar QR Code",
        "pdf.qrgen.desc": "Gere uma imagem de QR Code a partir de qualquer texto ou URL.",
        "pdf.qrgen.ph": "Texto ou URL para o QR Code",
        "pdf.qrgen.action": "Gerar QR Code",
        "pdf.qrread.title": "Ler QR Code",
        "pdf.qrread.desc": "Envie uma imagem de QR Code para ler seu conteúdo.",
        "pdf.qrread.action": "Ler QR Code",
        "pdf.palette.title": "Extrair Paleta de Cores",
        "pdf.palette.desc": "Extraia até 6 cores dominantes de qualquer imagem em código HEX.",
        "pdf.palette.action": "Extrair Cores",
        "pdf.mp4.title": "Converter MP4 para MP3",
        "pdf.mp4.desc": "Extraia o áudio MP3 de um vídeo MP4.",
        "pdf.mp4.action": "Extrair Áudio MP3",

        // --- Modificar Arquivos (file_tools.html) ---
        "file.header.title": "Modificar <em>Arquivos</em>",
        "file.header.sub": "Comprima, proteja com senha, criptografe e manipule seus arquivos com segurança.",
        "file.sec.arch": "Arquivos e Pacotes",
        "file.zip.title": "Comprimir Arquivos",
        "file.zip.desc": "Selecione vários arquivos e comprima-os em um único ZIP ou TAR.GZ.",
        "file.zip.action": "Comprimir e baixar",
        "file.zippass.title": "ZIP com Senha",
        "file.zippass.desc": "Crie um arquivo ZIP protegido com criptografia AES-256. Ideal para enviar dados sensíveis.",
        "file.zippass.ph": "Senha para proteger o ZIP",
        "file.zippass.action": "Proteger e baixar",
        "file.enc.title": "Criptografar Arquivo",
        "file.enc.desc": "Criptografe qualquer arquivo com AES-256-CBC. Só quem tiver a senha poderá abrir.",
        "file.enc.ph": "Senha de criptografia",
        "file.enc.action": "Criptografar e baixar .enc",
        "file.dec.title": "Descriptografar Arquivo",
        "file.dec.desc": "Descriptografe arquivos .enc gerados pelo Prisma (necessita da senha original).",
        "file.dec.choose": "Escolher Arquivo .enc",
        "file.dec.ph": "Senha usada na criptografia",
        "file.dec.action": "Descriptografar e baixar",
        "file.hash.title": "Calculadora de Hash",
        "file.hash.desc": "Calcule as impressões digitais (checksums) de qualquer arquivo.",
        "file.hash.action": "Calcular Hash",
        "file.rename.title": "Renomear Arquivos em Lote",
        "file.rename.desc": "Adicione um prefixo padronizado a múltiplos arquivos simultaneamente.",
        "file.rename.ph": "Novo prefixo para os arquivos",
        "file.rename.action": "Renomear e baixar ZIP",

        // --- General ---
        "footer.rights": "Prisma © 2026",
        "footer.by": "Made by Gustavo Goulart",
        "toast.done": "Download concluído!",
        "file.none": "Nenhum arquivo selecionado",
        "err.404": "Ops! A página que você está procurando não existe ou mudou de endereço.",
        "err.500": "Ops! Ocorreu um erro interno no servidor ao processar sua requisição."
    },
    en: {
        // --- Navigation & Sidebar ---
        "nav.home": "Home",
        "nav.converter": "File Converter",
        "nav.advanced": "Advanced Tools",
        "nav.modify": "Modify Files",
        "sidebar.menu": "Menu",
        "sidebar.limit": "Limit",
        "sidebar.conversions": "Conversions",
        "sidebar.theme": "Theme",
        "sidebar.language": "Language",

        // --- Home Page ---
        "home.title": "You think it.<br><em>Prisma does it.</em>",
        "home.subtitle": "From conversions to new possibilities. Everything for your files, in one place.",
        "home.card1.title": "File Converter",
        "home.card1.desc": "Convert documents (PDF, DOCX, XLSX, PPTX, CSV), images (PNG, JPG, WEBP, HEIC) and JSON data files fast.",
        "home.card1.btn": "Open Converter",
        "home.card2.title": "Advanced Tools",
        "home.card2.desc": "Generate and read custom QR Codes, extract dominant color palettes from images and convert MP4 video to MP3 audio.",
        "home.card2.btn": "Open Tools",
        "home.card3.title": "Modify Files",
        "home.card3.desc": "Compress files into ZIP / TAR.GZ, password-protect files, encrypt with AES-256, calculate Hash and batch rename.",
        "home.card3.btn": "Open Modifier",
        "home.feat1.title": "Guaranteed Privacy",
        "home.feat1.desc": "Local and secure processing. Your files are never stored permanently or shared with third parties.",
        "home.feat2.title": "No Account Needed",
        "home.feat2.desc": "Immediate and free access to all features. No sign-ups, no forms, no hassle.",
        "home.feat3.title": "Unified Ecosystem",
        "home.feat3.desc": "Everything you need for file conversion, manipulation, security, and analysis in a modern unified interface.",

        // --- Converter (index.html) ---
        "conv.header.title": "File <em>Converter</em>",
        "conv.header.sub": "Convert documents, images, and multi-format data quickly, directly, and 100% locally.",
        "conv.step1.label": "Select file",
        "conv.upload.drag": "Drag & drop file here",
        "conv.upload.btn": "Upload",
        "conv.step2.label": "Choose target format",
        "conv.ori.title": "PDF ORIENTATION",
        "conv.ori.portrait": "Portrait",
        "conv.ori.landscape": "Landscape",
        "conv.btn.convert": "Convert & Download",
        "conv.btn.another": "Convert another file",
        "conv.history.title": "Session history",
        "conv.history.unit": "conversion(s)",
        "conv.preview.label": "Preview",
        "conv.preview.empty": "No file uploaded",
        "conv.preview.emptySub": "Preview appears here.<br>Click on a format to see how it looks.",

        // --- Advanced Tools (pdf_tools.html) ---
        "pdf.header.title": "Advanced <em>Tools</em>",
        "pdf.header.sub": "Powerful utilities for fast, local document and image processing.",
        "pdf.sec.pdf": "PDF Tools",
        "pdf.merge.title": "Merge PDFs",
        "pdf.merge.desc": "Select multiple PDF files and combine them into a single continuous document. You can click multiple times to add more files.",
        "pdf.merge.choose": "Choose Files",
        "pdf.merge.action": "Merge & Download",
        "pdf.split.title": "Split PDF",
        "pdf.split.desc": "Separate each page of a PDF into independent files (delivered in a ZIP).",
        "pdf.split.choose": "Choose File",
        "pdf.split.opt.ind": "Page by page",
        "pdf.split.opt.fix": "Every N pages",
        "pdf.split.opt.cust": "Specific pages",
        "pdf.split.action": "Split & Download ZIP",
        "pdf.protect.title": "Protect PDF",
        "pdf.protect.desc": "Add a strong password to encrypt and restrict PDF access.",
        "pdf.protect.ph": "Desired password",
        "pdf.protect.action": "Protect & Download",
        "pdf.unprotect.title": "Unlock PDF",
        "pdf.unprotect.desc": "Remove password from an encrypted PDF (original password required).",
        "pdf.unprotect.ph": "PDF Password",
        "pdf.unprotect.action": "Unlock & Download",
        "pdf.compress.title": "Compress PDF",
        "pdf.compress.desc": "Reduce PDF file size by optimizing embedded images.",
        "pdf.compress.action": "Compress & Download",
        "pdf.wm.title": "PDF Watermark",
        "pdf.wm.desc": "Add a text watermark to all pages of your PDF document.",
        "pdf.wm.ph": "Watermark text",
        "pdf.wm.action": "Apply & Download",
        "pdf.extract.title": "Extract PDF Images",
        "pdf.extract.desc": "Extract all embedded images from a PDF. Returns a ZIP file.",
        "pdf.extract.action": "Extract & Download ZIP",
        "pdf.sec.media": "Images & Media",
        "pdf.qrgen.title": "Generate QR Code",
        "pdf.qrgen.desc": "Generate a QR Code image from any text or URL.",
        "pdf.qrgen.ph": "Text or URL for QR Code",
        "pdf.qrgen.action": "Generate QR Code",
        "pdf.qrread.title": "Read QR Code",
        "pdf.qrread.desc": "Upload a QR Code image to read its contents.",
        "pdf.qrread.action": "Read QR Code",
        "pdf.palette.title": "Extract Color Palette",
        "pdf.palette.desc": "Extract up to 6 dominant colors from any image in HEX format.",
        "pdf.palette.action": "Extract Colors",
        "pdf.mp4.title": "Convert MP4 to MP3",
        "pdf.mp4.desc": "Extract MP3 audio track from an MP4 video file.",
        "pdf.mp4.action": "Extract MP3 Audio",

        // --- Modify Files (file_tools.html) ---
        "file.header.title": "Modify <em>Files</em>",
        "file.header.sub": "Compress, password-protect, encrypt, and manipulate your files securely.",
        "file.sec.arch": "Files & Archives",
        "file.zip.title": "Compress Files",
        "file.zip.desc": "Select multiple files and compress them into a single ZIP or TAR.GZ archive.",
        "file.zip.action": "Compress & Download",
        "file.zippass.title": "Password Protected ZIP",
        "file.zippass.desc": "Create a ZIP archive encrypted with AES-256. Ideal for sensitive data.",
        "file.zippass.ph": "Password to protect ZIP",
        "file.zippass.action": "Protect & Download",
        "file.enc.title": "Encrypt File",
        "file.enc.desc": "Encrypt any file with AES-256-CBC. Only password holders can open it.",
        "file.enc.ph": "Encryption password",
        "file.enc.action": "Encrypt & Download .enc",
        "file.dec.title": "Decrypt File",
        "file.dec.desc": "Decrypt .enc files created with Prisma (original password required).",
        "file.dec.choose": "Choose .enc File",
        "file.dec.ph": "Password used for encryption",
        "file.dec.action": "Decrypt & Download",
        "file.hash.title": "Hash Calculator",
        "file.hash.desc": "Calculate digital fingerprints (checksums) for any file.",
        "file.hash.action": "Calculate Hash",
        "file.rename.title": "Batch Rename Files",
        "file.rename.desc": "Add a standardized prefix to multiple files simultaneously.",
        "file.rename.ph": "New prefix for files",
        "file.rename.action": "Rename & Download ZIP",

        // --- General ---
        "footer.rights": "Prisma © 2026",
        "footer.by": "Made by Gustavo Goulart",
        "toast.done": "Download complete!",
        "file.none": "No file selected",
        "err.404": "Oops! The page you are looking for does not exist or has moved.",
        "err.500": "Oops! An internal server error occurred while processing your request."
    },
    es: {
        // --- Navegación y Sidebar ---
        "nav.home": "Inicio",
        "nav.converter": "Conversor de archivos",
        "nav.advanced": "Herramientas Avanzadas",
        "nav.modify": "Modificar Archivos",
        "sidebar.menu": "Menú",
        "sidebar.limit": "Límite",
        "sidebar.conversions": "Conversiones",
        "sidebar.theme": "Tema",
        "sidebar.language": "Idioma",

        // --- Home Page ---
        "home.title": "Tú lo piensas.<br><em>Prisma lo hace.</em>",
        "home.subtitle": "De conversiones a nuevas posibilidades. Todo para tus archivos, en un solo lugar.",
        "home.card1.title": "Conversor de Archivos",
        "home.card1.desc": "Convierte documentos (PDF, DOCX, XLSX, PPTX, CSV), imágenes (PNG, JPG, WEBP, HEIC) y archivos JSON rápidamente.",
        "home.card1.btn": "Acceder al Conversor",
        "home.card2.title": "Herramientas Avanzadas",
        "home.card2.desc": "Genera y lee códigos QR personalizados, extrae la paleta de colores dominantes de imágenes y convierte video MP4 a audio MP3.",
        "home.card2.btn": "Acceder a Herramientas",
        "home.card3.title": "Modificar Archivos",
        "home.card3.desc": "Comprime archivos en ZIP / TAR.GZ, protege con contraseña, encripta con AES-256, calcula Hash y renombra en lote.",
        "home.card3.btn": "Acceder al Modificador",
        "home.feat1.title": "Privacidad Garantizada",
        "home.feat1.desc": "Procesamiento seguro y local. Tus archivos nunca se almacenan permanentemente ni se comparten con terceros.",
        "home.feat2.title": "Sin Necesidad de Cuenta",
        "home.feat2.desc": "Acceso inmediato y gratuito a todas las funciones. Sin registros, sin formularios, sin complicaciones.",
        "home.feat3.title": "Ecosistema Unificado",
        "home.feat3.desc": "Todo lo que necesitas para conversión, manipulación, seguridad y análisis de archivos en una sola interfaz moderna.",

        // --- Conversor (index.html) ---
        "conv.header.title": "Conversor de <em>Archivos</em>",
        "conv.header.sub": "Convierte documentos, imágenes y datos multiformato de manera rápida, directa y 100% local.",
        "conv.step1.label": "Selecciona el archivo",
        "conv.upload.drag": "Arrastra el archivo aquí",
        "conv.upload.btn": "Enviar",
        "conv.step2.label": "Elige el formato de destino",
        "conv.ori.title": "ORIENTACIÓN DEL PDF",
        "conv.ori.portrait": "Retrato",
        "conv.ori.landscape": "Paisaje",
        "conv.btn.convert": "Convertir y descargar",
        "conv.btn.another": "Convertir otro archivo",
        "conv.history.title": "Historial de la sesión",
        "conv.history.unit": "conversión(es)",
        "conv.preview.label": "Vista previa",
        "conv.preview.empty": "Ningún archivo enviado",
        "conv.preview.emptySub": "La vista previa aparece aquí.<br>Haz clic en un formato para ver cómo quedará.",

        // --- Herramientas Avanzadas (pdf_tools.html) ---
        "pdf.header.title": "Herramientas <em>Avanzadas</em>",
        "pdf.header.sub": "Utilidades potentes para procesamiento rápido y local de documentos e imágenes.",
        "pdf.sec.pdf": "Herramientas PDF",
        "pdf.merge.title": "Unir PDFs",
        "pdf.merge.desc": "Selecciona múltiples archivos PDF y únelos en un solo documento continuo. Puedes hacer clic varias veces para añadir más archivos.",
        "pdf.merge.choose": "Elegir Archivos",
        "pdf.merge.action": "Unir y descargar",
        "pdf.split.title": "Dividir PDF",
        "pdf.split.desc": "Separa cada página de un PDF en archivos independientes (entregados en ZIP).",
        "pdf.split.choose": "Elegir Archivo",
        "pdf.split.opt.ind": "Página por página",
        "pdf.split.opt.fix": "Cada N páginas",
        "pdf.split.opt.cust": "Páginas específicas",
        "pdf.split.action": "Dividir y descargar ZIP",
        "pdf.protect.title": "Proteger PDF",
        "pdf.protect.desc": "Añade una contraseña fuerte para encriptar y restringir la apertura del PDF.",
        "pdf.protect.ph": "Contraseña deseada",
        "pdf.protect.action": "Proteger y descargar",
        "pdf.unprotect.title": "Desbloquear PDF",
        "pdf.unprotect.desc": "Quita la contraseña de un PDF encriptado (requiere la contraseña original).",
        "pdf.unprotect.ph": "Contraseña del PDF",
        "pdf.unprotect.action": "Desbloquear y descargar",
        "pdf.compress.title": "Comprimir PDF",
        "pdf.compress.desc": "Reduce el tamaño de tu PDF optimizando las imágenes internas.",
        "pdf.compress.action": "Comprimir y descargar",
        "pdf.wm.title": "Marca de Agua PDF",
        "pdf.wm.desc": "Añade una marca de agua en texto en todas las páginas de tu PDF.",
        "pdf.wm.ph": "Texto de la marca de agua",
        "pdf.wm.action": "Aplicar y descargar",
        "pdf.extract.title": "Extraer Imágenes PDF",
        "pdf.extract.desc": "Extrae todas las imágenes integradas en un PDF. Devuelve un archivo ZIP.",
        "pdf.extract.action": "Extraer y descargar ZIP",
        "pdf.sec.media": "Imágenes y Medios",
        "pdf.qrgen.title": "Generar Código QR",
        "pdf.qrgen.desc": "Genera una imagen de código QR a partir de cualquier texto o URL.",
        "pdf.qrgen.ph": "Texto o URL para el código QR",
        "pdf.qrgen.action": "Generar Código QR",
        "pdf.qrread.title": "Leer Código QR",
        "pdf.qrread.desc": "Envía una imagen con un código QR para leer su contenido.",
        "pdf.qrread.action": "Leer Código QR",
        "pdf.palette.title": "Extraer Paleta de Colores",
        "pdf.palette.desc": "Extrae hasta 6 colores dominantes de cualquier imagen en código HEX.",
        "pdf.palette.action": "Extraer Colores",
        "pdf.mp4.title": "Convertir MP4 a MP3",
        "pdf.mp4.desc": "Extrae el audio MP3 de un video MP4.",
        "pdf.mp4.action": "Extraer Audio MP3",

        // --- Modificar Archivos (file_tools.html) ---
        "file.header.title": "Modificar <em>Archivos</em>",
        "file.header.sub": "Comprime, protege con contraseña, encripta y manipula tus archivos de forma segura.",
        "file.sec.arch": "Archivos y Paquetes",
        "file.zip.title": "Comprimir Archivos",
        "file.zip.desc": "Selecciona múltiples archivos y comprímelos en un solo ZIP o TAR.GZ.",
        "file.zip.action": "Comprimir y descargar",
        "file.zippass.title": "ZIP con Contraseña",
        "file.zippass.desc": "Crea un archivo ZIP protegido con encriptación AES-256. Ideal para datos sensibles.",
        "file.zippass.ph": "Contraseña para el ZIP",
        "file.zippass.action": "Proteger y descargar",
        "file.enc.title": "Encriptar Archivo",
        "file.enc.desc": "Encripta cualquier archivo con AES-256-CBC. Solo quien tenga la contraseña podrá abrirlo.",
        "file.enc.ph": "Contraseña de encriptación",
        "file.enc.action": "Encriptar y descargar .enc",
        "file.dec.title": "Desencriptar Archivo",
        "file.dec.desc": "Desencripta archivos .enc creados con Prisma (requiere la contraseña original).",
        "file.dec.choose": "Elegir Archivo .enc",
        "file.dec.ph": "Contraseña usada en la encriptación",
        "file.dec.action": "Desencriptar y descargar",
        "file.hash.title": "Calculadora de Hash",
        "file.hash.desc": "Calcula huellas digitales (checksums) de cualquier archivo.",
        "file.hash.action": "Calcular Hash",
        "file.rename.title": "Renombrar Archivos en Lote",
        "file.rename.desc": "Añade un prefijo estandarizado a múltiples archivos simultáneamente.",
        "file.rename.ph": "Nuevo prefijo para los archivos",
        "file.rename.action": "Renombrar y descargar ZIP",

        // --- General ---
        "footer.rights": "Prisma © 2026",
        "footer.by": "Hecho por Gustavo Goulart",
        "toast.done": "¡Descarga completada!",
        "file.none": "Ningún archivo seleccionado",
        "err.404": "¡Ups! La página que buscas no existe o ha cambiado de dirección.",
        "err.500": "¡Ups! Ocurrió un error interno en el servidor al procesar tu solicitud."
    }
};

function getCurrentLang() {
    const saved = localStorage.getItem("prisma_lang");
    if (saved && ["pt", "en", "es"].includes(saved)) return saved;
    const browserLang = (navigator.language || "").slice(0, 2).toLowerCase();
    if (["en", "es"].includes(browserLang)) return browserLang;
    return "pt";
}

function setLanguage(lang) {
    if (!translations[lang]) lang = "pt";
    localStorage.setItem("prisma_lang", lang);
    document.documentElement.setAttribute("lang", lang === "pt" ? "pt-BR" : lang === "en" ? "en-US" : "es");

    const dict = translations[lang];

    // Atualiza texto dos elementos com data-i18n
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (dict[key]) {
            el.innerHTML = dict[key];
        }
    });

    // Atualiza placeholders
    document.querySelectorAll("[data-i18n-ph]").forEach(el => {
        const key = el.getAttribute("data-i18n-ph");
        if (dict[key]) {
            el.placeholder = dict[key];
        }
    });

    // Atualiza botões seletores de idioma na UI
    document.querySelectorAll(".btn-lang-opt").forEach(btn => {
        const btnLang = btn.getAttribute("data-lang");
        if (btnLang === lang) {
            btn.classList.add("ativo");
        } else {
            btn.classList.remove("ativo");
        }
    });

    // Dispara evento customizado para outros scripts
    window.dispatchEvent(new CustomEvent("languageChanged", { detail: { lang, dict } }));
}

document.addEventListener("DOMContentLoaded", () => {
    const lang = getCurrentLang();
    setLanguage(lang);

    // Event listeners nos botões de idioma
    document.addEventListener("click", (e) => {
        const btn = e.target.closest(".btn-lang-opt");
        if (btn) {
            const targetLang = btn.getAttribute("data-lang");
            if (targetLang) setLanguage(targetLang);
        }
    });
});
