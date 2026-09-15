/**
 * i18n.js — Sistema Completo de Internacionalização (Português, Inglês, Espanhol)
 * Prisma Audio — Suíte Universal de Áudio
 */

const translations = {
    pt: {
        "nav.history": "Histórico de Arquivos",
        "conv.history.title": "Histórico da Sessão",
        "conv.history.unit": "arquivo(s)",
        "conv.history.deleted": "Conteúdo Apagado",
        "conv.history.restore": "Restaurar ↺",
        "conv.history.restored": "Restaurado",
        "conv.history.restoreToast": "Arquivo restaurado com sucesso! Cronômetro reiniciado.",
        "conv.history.expired": "TEMPO ESGOTADO",
        "conv.security.title": "Autodestruição e segurança",
        "conv.security.retention": "PADRÃO PARA NOVOS ENVIOS",
        "conv.selfdestruct.instant": "Download único",
        "conv.selfdestruct.5min": "TIMER 5 MIN",
        "conv.selfdestruct.15min": "PADRÃO 15 MIN",
        "conv.selfdestruct.15minDefault": "15 min (Padrão)",
        "history.header.title": "Histórico de <em>Arquivos</em>",
        "history.header.sub": "Gerencie seus arquivos processados, acompanhe a contagem de autodestruição e restaure retenções.",
        "history.batch.title": "Ações em lote",
        "history.batch.downloadAll": "Baixar todos (ZIP)",
        "history.batch.destroyAll": "Destruir tudo agora",
        "history.empty.title": "Seu histórico está vazio",
        "history.empty.sub": "Faça o upload ou conversão de arquivos para visualizá-los e gerenciá-los nesta aba.",
        "history.destroyModal.label": "Ação irreversível",
        "history.destroyModal.title": "Destruir todos os arquivos?",
        "history.destroyModal.desc": "Os arquivos ativos desta sessão serão removidos agora com Zero-Fill seguro.",
        "history.destroyModal.cancel": "Cancelar",
        "history.destroyModal.confirm": "Destruir permanentemente",

        // --- Navegação & Sidebar ---
        "nav.home": "Início",
        "nav.converter": "Conversor de Arquivos",
        "nav.advanced": "Ferramentas Avançadas",
        "nav.audio_tools": "Ferramentas de Áudio",
        "nav.video_tools": "Ferramentas de Vídeo",
        "sidebar.menu": "NAVEGAÇÃO",
        "sidebar.theme": "Tema",
        "sidebar.language": "Idioma",

        // --- Personalização ---
        "customizer.title": "Personalizar Aparência",
        "customizer.subtitle": "Escolha o idioma, modo de exibição e a cor de destaque do sistema",
        "customizer.lang.title": "Idioma do Sistema",
        "customizer.lang.pt": "Português (Brasil)",
        "customizer.lang.en": "English",
        "customizer.lang.es": "Español",
        "customizer.mode.title": "Modo de Exibição",
        "customizer.mode.dark": "Escuro",
        "customizer.mode.light": "Claro",
        "customizer.accent.title": "Cor Principal do Site",
        "customizer.accent.darkSub": "Cores otimizadas para o modo escuro",
        "customizer.accent.lightSub": "Cores otimizadas para o modo claro",
        "customizer.done": "Concluído",

        // --- Home Page ---
        "home.title": "Você pensa.<br><em>O Prisma faz.</em>",
        "home.subtitle": "De conversões a utilitários avançados. Tudo para seus arquivos em uma única plataforma.",
        "home.card1.title": "Ferramentas de Áudio",
        "home.card1.desc": "Converta, corte, junte, transcreva áudio em texto (AI), normalize, acelere e inverta seus arquivos instantaneamente.",
        "home.card1.btn": "Acessar Ferramentas",
        "home.card2.title": "Ferramentas de Vídeo",
        "home.card2.desc": "Utilitários de alta performance para converter MP4 para MP3, criar GIFs animados e baixar vídeos via URL.",
        "home.card2.btn": "Acessar Ferramentas",

        "home.card3.title": "Prisma Conversor de Arquivo",
        "home.card3.desc": "Acesse a suíte universal de conversão de documentos, PDFs, planilhas e imagens.",
        "home.card3.btn": "Ir para o Prisma Conversor",
        "home.feat1.title": "Privacidade e Segurança",
        "home.feat1.desc": "Processamento temporário e seguro. Seus arquivos são descartados automaticamente e nunca compartilhados.",
        "home.feat2.title": "Sem Necessidade de Cadastro",
        "home.feat2.desc": "Acesso livre e imediato a todos os recursos. Sem necessidade de criar conta, preencher formulários ou pagar nada.",
        "home.feat3.title": "Plataforma Integrada",
        "home.feat3.desc": "Todas as ferramentas essenciais para manipulação e processamento de áudio em uma interface moderna e veloz.",

        // --- Audio Tools & Controls ---
        "audio.dropzone": "Arraste o arquivo aqui",
        "audio.header.title": "Ferramentas <em>de Áudio</em>",
        "audio.header.sub": "Utilitários especializados para conversão, corte, junção, ajuste de volume, velocidade e inversão de mídias.",
        "audio.conv.title": "Conversor Universal",
        "audio.conv.desc": "Converte entre MP3, WAV, AAC, OGG, FLAC, M4A e OPUS com escolha de taxa de bits.",
        "audio.conv.output_format": "FORMATO DE SAÍDA",
        "audio.conv.bitrate": "TAXA DE BITS",
        "audio.conv.channels": "CANAIS DE ÁUDIO",
        "audio.conv.sample_rate": "TAXA DE AMOSTRAGEM",
        "audio.conv.stereo": "Estéreo (2.0)",
        "audio.conv.mono": "Mono (1.0)",
        "audio.conv.hud_title": "MODO DE PROCESSAMENTO E LEGENDA TÉCNICA",
        "audio.conv.legend_bitrate_title": "• Taxa de Bits (Bitrate):",
        "audio.conv.legend_bitrate_desc": "Quanto maior (ex: 320k), maior a clareza e fidelidade dos áudios. 192k é o equilíbrio ideal.",
        "audio.conv.legend_sample_title": "• Amostragem (kHz):",
        "audio.conv.legend_sample_desc": "44.1 kHz é o padrão de CD e músicas. 48.0 kHz é o padrão profissional para vídeos e estúdio.",
        "audio.conv.legend_channels_title": "• Canais (2.0 / 1.0):",
        "audio.conv.legend_channels_desc": "Estéreo (2.0) separa som em fone esquerdo/direito. Mono (1.0) une os canais para podcasts leves.",
        "audio.conv.fmt_mp3": "MP3 — Mais compatível",
        "audio.conv.fmt_wav": "WAV — Sem compressão (Lossless)",
        "audio.conv.fmt_aac": "AAC — Alta eficiência (Apple/Streaming)",
        "audio.conv.fmt_ogg": "OGG — Open source",
        "audio.conv.fmt_flac": "FLAC — Lossless comprimido",
        "audio.conv.fmt_m4a": "M4A — Apple/iOS",
        "audio.conv.fmt_opus": "OPUS — Streaming moderno",
        "audio.conv.btn": "Converter Áudio",

        "audio.cut.title": "Cortador de Áudio",
        "audio.cut.desc": "Corta trechos exatos especificando tempo inicial e final (ex: 0:10 a 1:30).",
        "audio.cut.preview": "Ouvir Trecho Selecionado",
        "audio.cut.start_slider": "Início do corte (arraste a barra):",
        "audio.cut.end_slider": "Fim do corte (arraste a barra):",
        "audio.cut.start_time": "TEMPO INICIAL",
        "audio.cut.end_time": "TEMPO FINAL",
        "audio.cut.btn": "Cortar Áudio",

        "audio.join.title": "Juntador de Áudios",
        "audio.join.desc": "Combina 2 ou mais arquivos de áudio em uma única faixa sequencial.",
        "audio.join.dropzone": "Arraste múltiplos arquivos aqui ou clique para selecionar",
        "audio.join.add_btn": "+ Adicionar mais áudios",
        "audio.join.btn": "Juntar Áudios",

        "audio.vol.title": "Aumentador de Volume & Normalizador",
        "audio.vol.desc": "Aumenta +3dB, +6dB, +12dB ou normaliza o volume via EBU R128.",
        "audio.vol.boost_label": "AJUSTE DE VOLUME / GANHO",
        "audio.vol.btn": "Ajustar Volume",

        "audio.speed.title": "Alterador de Velocidade",
        "audio.speed.desc": "Acelera ou desacelera de 0.5x a 2.0x sem alterar o tom da voz (time-stretch).",
        "audio.speed.factor_label": "FATOR DE VELOCIDADE",
        "audio.speed.btn": "Alterar Velocidade",

        "audio.rev.title": "Inversor de Áudio",
        "audio.rev.desc": "Toca o áudio de trás para frente — ideal para efeitos sonoros e memes.",
        "audio.rev.warn": "Atenção: inverter arquivos FLAC grandes pode levar mais tempo, pois todo o áudio precisa ser carregado na memória antes de ser invertido.",
        "audio.rev.btn": "Inverter Áudio",

        "audio.trns.title": "Transcritor de Áudio (Speech-to-Text)",
        "audio.trns.desc": "Converte áudio em texto escrito, transcrição automática e geração de legendas (.txt, .srt, .json).",
        "audio.trns.lang_label": "IDIOMA DO ÁUDIO",
        "audio.trns.fmt_label": "FORMATO DE SAÍDA",
        "audio.trns.preview_label": "TRANSCRIÇÃO EM TEMPO REAL",
        "audio.trns.btn_copy": "Copiar Texto",
        "audio.trns.btn": "Transcrever Áudio",

        // --- Ferramentas de Vídeo ---
        "video.header.title": "Ferramentas <em>de Vídeo</em>",
        "video.header.sub": "Extraia áudio em MP3, crie GIFs animados de alta qualidade e baixe vídeos por link de plataformas sociais.",
        "video.tab.mp4_mp3": "MP4 para MP3",
        "video.mp3.desc": "Extraia a faixa de áudio de arquivos de vídeo MP4, MKV ou WebM em áudio MP3 cristalino.",
        "video.mp3.btn_select": "Selecionar Arquivo de Vídeo",
        "video.mp3.bitrate": "QUALIDADE / BITRATE",
        "video.mp3.btn_exec": "Extrair Áudio MP3",
        "video.tab.mp4_gif": "MP4 para GIF",
        "video.gif.desc": "Transforme vídeos ou trechos específicos em animações GIF otimizadas de alta qualidade.",
        "video.gif.btn_select": "Selecionar Arquivo MP4",
        "video.gif.start_label": "TEMPO INICIAL (S)",
        "video.gif.duration_label": "DURAÇÃO (S)",
        "video.gif.fps_label": "TAXA DE QUADROS (FPS)",
        "video.gif.width_label": "LARGURA (PX)",
        "video.gif.btn_exec": "Gerar GIF Animado",
        "video.tab.downloader": "Baixar Vídeos por Link",
        "video.dl.desc": "Baixe vídeos e áudios com alta velocidade via URL pública do YouTube, Twitter/X, Instagram e TikTok.",
        "video.dl.url_label": "URL DO VÍDEO",
        "video.dl.url_ph": "Cole o link do vídeo aqui (ex: https://youtube.com/watch?... ou https://x.com/...)",
        "video.dl.format": "FORMATO DESEJADO",
        "video.dl.quality": "QUALIDADE DE VÍDEO",
        "video.dl.quality_audio": "QUALIDADE DO ÁUDIO",
        "video.dl.q_best": "Melhor Qualidade",
        "video.dl.q_1080p": "1080p Full HD",
        "video.dl.q_720p": "720p HD",
        "video.dl.q_480p": "480p SD",
        "video.dl.btn_exec": "Baixar Mídia por Link",

        "video.tab.converter": "Conversor de Formato",
        "video.conv.desc": "Converte vídeos entre MP4, WEBM, MOV, AVI e MKV com alta qualidade.",
        "video.conv.fmt_label": "FORMATO DE SAÍDA",
        "video.conv.btn_exec": "Converter Formato",

        "video.tab.compressor": "Compressor de Vídeo",
        "video.comp.desc": "Reduza o tamanho do arquivo mantendo a qualidade de imagem ideal.",
        "video.comp.level_label": "NÍVEL DE COMPRESSÃO",
        "video.comp.l_wa": "WhatsApp / Discord (~70%)",
        "video.comp.l_med": "Compressão Média (~50%)",
        "video.comp.l_light": "Compressão Leve (~30%)",
        "video.comp.btn_exec": "Comprimir Vídeo",

        "video.tab.mute": "Silenciar / Remover Áudio",
        "video.mute.desc": "Remove a faixa de áudio do vídeo sem re-codificar (velocidade máxima).",
        "video.mute.btn_exec": "Silenciar Vídeo",

        "video.tab.snap": "Capturar Foto do Vídeo",
        "video.snap.desc": "Extraia um frame / foto HD do vídeo em qualquer segundo desejado.",
        "video.snap.time_label": "SEGUNDO DO VÍDEO (S)",
        "video.snap.fmt_label": "FORMATO DA IMAGEM",
        "video.snap.btn_exec": "Capturar Imagem",

        // --- Gerais ---
        "footer.rights": "Prisma Audio © 2026",
        "footer.by": "Desenvolvido por Gustavo Goulart",
        "toast.done": "Processamento concluído com sucesso!",
        "file.none": "Nenhum arquivo selecionado"
    },

    en: {
        "nav.history": "File History",
        "conv.history.title": "Session History",
        "conv.history.unit": "file(s)",
        "conv.history.deleted": "Content Deleted",
        "conv.history.restore": "Restore ↺",
        "conv.history.restored": "Restored",
        "conv.history.restoreToast": "File successfully restored! Countdown restarted.",
        "conv.history.expired": "TIME EXPIRED",
        "conv.security.title": "Self-destruction & Security",
        "conv.security.retention": "DEFAULT FOR NEW UPLOADS",
        "conv.selfdestruct.instant": "Single Download",
        "conv.selfdestruct.5min": "5 MIN TIMER",
        "conv.selfdestruct.15min": "15 MIN DEFAULT",
        "conv.selfdestruct.15minDefault": "15 min (Default)",
        "history.header.title": "File <em>History</em>",
        "history.header.sub": "Manage your processed files, monitor self-destruction timers, and restore retention.",
        "history.batch.title": "Batch Actions",
        "history.batch.downloadAll": "Download all (ZIP)",
        "history.batch.destroyAll": "Destroy everything now",
        "history.empty.title": "Your history is empty",
        "history.empty.sub": "Upload or convert files to view and manage them in this tab.",
        "history.destroyModal.label": "Irreversible Action",
        "history.destroyModal.title": "Destroy all files?",
        "history.destroyModal.desc": "Active session files will be permanently erased now with Zero-Fill wipe.",
        "history.destroyModal.cancel": "Cancel",
        "history.destroyModal.confirm": "Destroy permanently",

        // --- Navigation & Sidebar ---
        "nav.home": "Home",
        "nav.converter": "File Converter",
        "nav.advanced": "Advanced Tools",
        "nav.audio_tools": "Audio Tools",
        "nav.video_tools": "Video Tools",
        "sidebar.menu": "NAVIGATION",
        "sidebar.theme": "Theme",
        "sidebar.language": "Language",

        // --- Customizer ---
        "customizer.title": "Customize Appearance",
        "customizer.subtitle": "Choose your language, display mode and system accent color",
        "customizer.lang.title": "System Language",
        "customizer.lang.pt": "Português (Brasil)",
        "customizer.lang.en": "English",
        "customizer.lang.es": "Español",
        "customizer.mode.title": "Display Mode",
        "customizer.mode.dark": "Dark",
        "customizer.mode.light": "Light",
        "customizer.accent.title": "Main Accent Color",
        "customizer.accent.darkSub": "Colors optimized for dark mode",
        "customizer.accent.lightSub": "Colors optimized for light mode",
        "customizer.done": "Done",

        // --- Home Page ---
        "home.title": "You think it.<br><em>Prisma does it.</em>",
        "home.subtitle": "From conversions to advanced utilities. Everything for your files on a single platform.",
        "home.card1.title": "Audio Tools",
        "home.card1.desc": "Convert, cut, join, transcribe audio to text (AI), normalize, speed up and reverse your audio files instantly.",
        "home.card1.btn": "Open Audio Tools",
        "home.card2.title": "Video Tools",
        "home.card2.desc": "High-performance utilities to convert MP4 to MP3, create animated GIFs, and download videos via link.",
        "home.card2.btn": "Open Video Tools",

        "home.card3.title": "Prisma File Converter",
        "home.card3.desc": "Access the universal suite for converting documents, PDFs, spreadsheets and images.",
        "home.card3.btn": "Go to Prisma Converter",
        "home.feat1.title": "Privacy & Security",
        "home.feat1.desc": "Temporary and safe processing. Your files are automatically discarded and never shared.",
        "home.feat2.title": "No Registration Required",
        "home.feat2.desc": "Free and immediate access to all features. No account creation, forms or payment needed.",
        "home.feat3.title": "Integrated Platform",
        "home.feat3.desc": "All essential tools for audio processing and manipulation in a modern, fast interface.",

        // --- Audio Tools & Controls ---
        "audio.dropzone": "Drag your file here",
        "audio.header.title": "Audio <em>Tools</em>",
        "audio.header.sub": "Specialized utilities for media conversion, cutting, merging, volume adjustment, speed control and reversing.",
        "audio.conv.title": "Universal Converter",
        "audio.conv.desc": "Converts between MP3, WAV, AAC, OGG, FLAC, M4A and OPUS with customizable bitrate.",
        "audio.conv.output_format": "OUTPUT FORMAT",
        "audio.conv.bitrate": "BITRATE",
        "audio.conv.channels": "AUDIO CHANNELS",
        "audio.conv.sample_rate": "SAMPLE RATE",
        "audio.conv.stereo": "Stereo (2.0)",
        "audio.conv.mono": "Mono (1.0)",
        "audio.conv.hud_title": "PROCESSING MODE & TECHNICAL LEGEND",
        "audio.conv.legend_bitrate_title": "• Bitrate:",
        "audio.conv.legend_bitrate_desc": "Higher values (e.g. 320k) yield greater audio clarity. 192k is the ideal balance.",
        "audio.conv.legend_sample_title": "• Sample Rate (kHz):",
        "audio.conv.legend_sample_desc": "44.1 kHz is standard CD/music quality. 48.0 kHz is professional video and studio standard.",
        "audio.conv.legend_channels_title": "• Channels (2.0 / 1.0):",
        "audio.conv.legend_channels_desc": "Stereo (2.0) separates left/right audio. Mono (1.0) merges channels for lightweight podcasts.",
        "audio.conv.fmt_mp3": "MP3 — Most Compatible",
        "audio.conv.fmt_wav": "WAV — Uncompressed (Lossless)",
        "audio.conv.fmt_aac": "AAC — High Efficiency (Apple/Streaming)",
        "audio.conv.fmt_ogg": "OGG — Open Source",
        "audio.conv.fmt_flac": "FLAC — Compressed Lossless",
        "audio.conv.fmt_m4a": "M4A — Apple/iOS",
        "audio.conv.fmt_opus": "OPUS — Modern Streaming",
        "audio.conv.btn": "Convert Audio",

        "audio.cut.title": "Audio Trimmer",
        "audio.cut.desc": "Cuts exact clips specifying start and end time (e.g., 0:10 to 1:30).",
        "audio.cut.preview": "Listen Selected Clip",
        "audio.cut.start_slider": "Start clip (drag slider):",
        "audio.cut.end_slider": "End clip (drag slider):",
        "audio.cut.start_time": "START TIME",
        "audio.cut.end_time": "END TIME",
        "audio.cut.btn": "Cut Audio",

        "audio.join.title": "Audio Merger",
        "audio.join.desc": "Combines 2 or more audio files into a single sequential track.",
        "audio.join.dropzone": "Drag multiple files here or click to select",
        "audio.join.add_btn": "+ Add more audio files",
        "audio.join.btn": "Merge Audios",

        "audio.vol.title": "Volume Booster & Normalizer",
        "audio.vol.desc": "Boosts volume (+3dB, +6dB, +12dB) or normalizes loudness via EBU R128.",
        "audio.vol.boost_label": "VOLUME ADJUSTMENT / GAIN",
        "audio.vol.btn": "Adjust Volume",

        "audio.speed.title": "Speed Changer",
        "audio.speed.desc": "Speed up or slow down from 0.5x to 2.0x without pitch distortion (time-stretch).",
        "audio.speed.factor_label": "SPEED FACTOR",
        "audio.speed.btn": "Change Speed",

        "audio.rev.title": "Audio Reverser",
        "audio.rev.desc": "Plays audio backwards — ideal for sound effects and creative audio.",
        "audio.rev.warn": "Note: reversing large FLAC files may take longer as all audio must be loaded into memory first.",
        "audio.rev.btn": "Reverse Audio",

        "audio.trns.title": "Audio Transcriber (Speech-to-Text)",
        "audio.trns.desc": "Converts audio to written text, automatic transcription and subtitle generation (.txt, .srt, .json).",
        "audio.trns.lang_label": "AUDIO LANGUAGE",
        "audio.trns.fmt_label": "OUTPUT FORMAT",
        "audio.trns.preview_label": "LIVE TRANSCRIPTION PREVIEW",
        "audio.trns.btn_copy": "Copy Text",
        "audio.trns.btn": "Transcribe Audio",

        // --- Video Tools ---
        "video.header.title": "Video <em>Tools</em>",
        "video.header.sub": "Extract MP3 audio, create high-quality animated GIFs and download videos by link from social platforms.",
        "video.tab.mp4_mp3": "MP4 to MP3",
        "video.mp3.desc": "Extract the audio track from MP4, MKV or WebM video files into crystal-clear MP3 audio.",
        "video.mp3.btn_select": "Select Video File",
        "video.mp3.bitrate": "QUALITY / BITRATE",
        "video.mp3.btn_exec": "Extract MP3 Audio",
        "video.tab.mp4_gif": "MP4 to GIF",
        "video.gif.desc": "Turn videos or specific clips into optimized high-quality GIF animations.",
        "video.gif.btn_select": "Select MP4 File",
        "video.gif.start_label": "START TIME (S)",
        "video.gif.duration_label": "DURATION (S)",
        "video.gif.fps_label": "FRAME RATE (FPS)",
        "video.gif.width_label": "WIDTH (PX)",
        "video.gif.btn_exec": "Generate Animated GIF",
        "video.tab.downloader": "Download Video by Link",
        "video.dl.desc": "Download videos and audio at high speed via public URL from YouTube, Twitter/X, Instagram and TikTok.",
        "video.dl.url_label": "VIDEO URL",
        "video.dl.url_ph": "Paste video link here (e.g. https://youtube.com/watch?... or https://x.com/...)",
        "video.dl.format": "DESIRED FORMAT",
        "video.dl.quality": "VIDEO QUALITY",
        "video.dl.quality_audio": "AUDIO QUALITY",
        "video.dl.q_best": "Best Quality",
        "video.dl.q_1080p": "1080p Full HD",
        "video.dl.q_720p": "720p HD",
        "video.dl.q_480p": "480p SD",
        "video.dl.btn_exec": "Download Media by Link",

        "video.tab.converter": "Format Converter",
        "video.conv.desc": "Convert videos between MP4, WEBM, MOV, AVI and MKV with high quality.",
        "video.conv.fmt_label": "OUTPUT FORMAT",
        "video.conv.btn_exec": "Convert Video Format",

        "video.tab.compressor": "Video Compressor",
        "video.comp.desc": "Reduce file size while keeping optimal visual quality.",
        "video.comp.level_label": "COMPRESSION LEVEL",
        "video.comp.l_wa": "WhatsApp / Discord (~70%)",
        "video.comp.l_med": "Medium Compression (~50%)",
        "video.comp.l_light": "Light Compression (~30%)",
        "video.comp.btn_exec": "Compress Video",

        "video.tab.mute": "Mute / Remove Audio",
        "video.mute.desc": "Remove audio track from video without re-encoding (max speed).",
        "video.mute.btn_exec": "Mute Video",

        "video.tab.snap": "Capture Photo from Video",
        "video.snap.desc": "Extract an HD frame / photo from the video at any desired second.",
        "video.snap.time_label": "VIDEO TIMESTAMP (S)",
        "video.snap.fmt_label": "IMAGE FORMAT",
        "video.snap.btn_exec": "Capture Image",

        // --- General ---
        "footer.rights": "Prisma Audio © 2026",
        "footer.by": "Developed by Gustavo Goulart",
        "toast.done": "Processing completed successfully!",
        "file.none": "No file selected"
    },

    es: {
        "nav.history": "Historial de Archivos",
        "conv.history.title": "Historial de la Sesión",
        "conv.history.unit": "archivo(s)",
        "conv.history.deleted": "Contenido Eliminado",
        "conv.history.restore": "Restaurar ↺",
        "conv.history.restored": "Restaurado",
        "conv.history.restoreToast": "¡Archivo restaurado con éxito! Temporizador reiniciado.",
        "conv.history.expired": "TIEMPO AGOTADO",
        "conv.security.title": "Autodestrucción y Seguridad",
        "conv.security.retention": "PREDETERMINADO PARA NUEVOS ENVÍOS",
        "conv.selfdestruct.instant": "Descarga única",
        "conv.selfdestruct.5min": "TEMPORIZADOR 5 MIN",
        "conv.selfdestruct.15min": "PREDETERMINADO 15 MIN",
        "conv.selfdestruct.15minDefault": "15 min (Predeterminado)",
        "history.header.title": "Historial de <em>Archivos</em>",
        "history.header.sub": "Administre sus archivos procesados, supervise temporizadores y restaure retenciones.",
        "history.batch.title": "Acciones en lote",
        "history.batch.downloadAll": "Descargar todos (ZIP)",
        "history.batch.destroyAll": "Destruir todo ahora",
        "history.empty.title": "Su historial está vacío",
        "history.empty.sub": "Suba o convierta archivos para verlos y administrarlos en esta pestaña.",
        "history.destroyModal.label": "Acción irreversible",
        "history.destroyModal.title": "¿Destruir todos los archivos?",
        "history.destroyModal.desc": "Los archivos activos de esta sesión se eliminarán ahora con borrado seguro Zero-Fill.",
        "history.destroyModal.cancel": "Cancelar",
        "history.destroyModal.confirm": "Destruir permanentemente",

        // --- Navegación ---
        "nav.home": "Inicio",
        "nav.converter": "Conversor de Archivos",
        "nav.advanced": "Herramientas Avanzadas",
        "nav.audio_tools": "Herramientas de Audio",
        "nav.video_tools": "Herramientas de Video",
        "sidebar.menu": "NAVEGACIÓN",
        "sidebar.theme": "Tema",
        "sidebar.language": "Idioma",

        // --- Personalización ---
        "customizer.title": "Personalizar Apariencia",
        "customizer.subtitle": "Elige tu idioma, modo de visualización y color de acento principal",
        "customizer.lang.title": "Idioma del Sistema",
        "customizer.lang.pt": "Português (Brasil)",
        "customizer.lang.en": "English",
        "customizer.lang.es": "Español",
        "customizer.mode.title": "Modo de Visualización",
        "customizer.mode.dark": "Oscuro",
        "customizer.mode.light": "Claro",
        "customizer.accent.title": "Color Principal del Sitio",
        "customizer.accent.darkSub": "Colores optimizados para modo oscuro",
        "customizer.accent.lightSub": "Colores optimizados para modo claro",
        "customizer.done": "Guardar",

        // --- Home Page ---
        "home.title": "Tú lo piensas.<br><em>Prisma lo hace.</em>",
        "home.subtitle": "Desde conversiones hasta herramientas avanzadas. Todo para tus archivos en una sola plataforma.",
        "home.card1.title": "Herramientas de Audio",
        "home.card1.desc": "Convierte, corta, une, transcribe audio a texto (AI), normaliza, acelera y revierte tus archivos de audio al instante.",
        "home.card1.btn": "Acceder a Herramientas",
        "home.card2.title": "Herramientas de Video",
        "home.card2.desc": "Nuevas herramientas avanzadas de audio y video con conversiones nativas.",
        "home.card2.btn": "Próximamente",
        "home.card3.title": "Prisma Conversor de Archivos",
        "home.card3.desc": "Accede a la suite universal para convertir documentos, PDFs, hojas de cálculo e imágenes.",
        "home.card3.btn": "Ir a Prisma Conversor",
        "home.feat1.title": "Privacidad y Seguridad",
        "home.feat1.desc": "Procesamiento temporal y seguro. Tus archivos se descartan automáticamente y nunca se comparten.",
        "home.feat2.title": "Sin Registro Necesario",
        "home.feat2.desc": "Acceso libre e inmediato a todas las funciones. Sin crear cuenta ni pagar nada.",
        "home.feat3.title": "Plataforma Integrada",
        "home.feat3.desc": "Todas las herramientas esenciales de procesamiento de audio en una interfaz moderna.",

        // --- Herramientas de Audio & Controles ---
        "audio.dropzone": "Arrastra el archivo aquí",
        "audio.header.title": "Herramientas <em>de Audio</em>",
        "audio.header.sub": "Utilidades especializadas para conversión, corte, unión, ajuste de volumen, velocidad e inversión.",
        "audio.conv.title": "Conversor Universal",
        "audio.conv.desc": "Convierte entre MP3, WAV, AAC, OGG, FLAC, M4A y OPUS con elección de tasa de bits.",
        "audio.conv.output_format": "FORMATO DE SALIDA",
        "audio.conv.bitrate": "TASA DE BITS",
        "audio.conv.channels": "CANALES DE AUDIO",
        "audio.conv.sample_rate": "TASA DE MUESTREO",
        "audio.conv.stereo": "Estéreo (2.0)",
        "audio.conv.mono": "Mono (1.0)",
        "audio.conv.hud_title": "MODO DE PROCESAMIENTO Y LEYENDA TÉCNICA",
        "audio.conv.legend_bitrate_title": "• Tasa de bits (Bitrate):",
        "audio.conv.legend_bitrate_desc": "A mayor valor (ej: 320k), mayor claridad y fidelidad. 192k es el equilibrio ideal.",
        "audio.conv.legend_sample_title": "• Muestreo (kHz):",
        "audio.conv.legend_sample_desc": "44.1 kHz es estándar de CD y música. 48.0 kHz es estándar profesional de video y estudio.",
        "audio.conv.legend_channels_title": "• Canales (2.0 / 1.0):",
        "audio.conv.legend_channels_desc": "Estéreo (2.0) separa sonido izquierdo/derecho. Mono (1.0) une canales para podcasts ligeros.",
        "audio.conv.fmt_mp3": "MP3 — Más Compatible",
        "audio.conv.fmt_wav": "WAV — Sin compresión (Lossless)",
        "audio.conv.fmt_aac": "AAC — Alta Eficiencia (Apple/Streaming)",
        "audio.conv.fmt_ogg": "OGG — Código Abierto",
        "audio.conv.fmt_flac": "FLAC — Lossless Comprimido",
        "audio.conv.fmt_m4a": "M4A — Apple/iOS",
        "audio.conv.fmt_opus": "OPUS — Streaming Moderno",
        "audio.conv.btn": "Convertir Audio",

        "audio.cut.title": "Cortador de Audio",
        "audio.cut.desc": "Corta fragmentos exactos especificando tiempo inicial y final (ej: 0:10 a 1:30).",
        "audio.cut.preview": "Escuchar Fragmento Seleccionado",
        "audio.cut.start_slider": "Inicio del corte (arrastra la barra):",
        "audio.cut.end_slider": "Fin del corte (arrastra la barra):",
        "audio.cut.start_time": "TIEMPO INICIAL",
        "audio.cut.end_time": "TIEMPO FINAL",
        "audio.cut.btn": "Cortar Audio",

        "audio.join.title": "Unidor de Audios",
        "audio.join.desc": "Combina 2 o más archivos de audio en una sola pista secuencial.",
        "audio.join.dropzone": "Arrastra múltiples archivos aquí o haz clic para seleccionar",
        "audio.join.add_btn": "+ Añadir más audios",
        "audio.join.btn": "Unir Audios",

        "audio.vol.title": "Amplificador de Volumen y Normalizador",
        "audio.vol.desc": "Aumenta +3dB, +6dB, +12dB o normaliza el volumen según EBU R128.",
        "audio.vol.boost_label": "AJUSTE DE VOLUMEN / GANANCIA",
        "audio.vol.btn": "Ajustar Volumen",

        "audio.speed.title": "Cambiador de Velocidad",
        "audio.speed.desc": "Acelera o desacelera de 0.5x a 2.0x sin alterar el tono de la voz.",
        "audio.speed.factor_label": "FACTOR DE VELOCIDAD",
        "audio.speed.btn": "Cambiar Velocidad",

        "audio.rev.title": "Inversor de Audio",
        "audio.rev.desc": "Reproduce el audio al revés — ideal para efectos de sonido y memes.",
        "audio.rev.warn": "Atención: invertir archivos FLAC grandes puede requerir más tiempo ya que todo el audio se carga en memoria primero.",
        "audio.rev.btn": "Invertir Audio",

        "audio.trns.title": "Transcriptor de Audio (Speech-to-Text)",
        "audio.trns.desc": "Convierte audio a texto escrito, transcripción automática y generación de subtítulos (.txt, .srt, .json).",
        "audio.trns.lang_label": "IDIOMA DEL AUDIO",
        "audio.trns.fmt_label": "FORMATO DE SALIDA",
        "audio.trns.preview_label": "VISTA PREVIA DE TRANSCRIPCIÓN",
        "audio.trns.btn_copy": "Copiar Texto",
        "audio.trns.btn": "Transcribir Audio",

        // --- Herramientas de Video ---
        "video.header.title": "Herramientas <em>de Video</em>",
        "video.header.sub": "Extrae audio MP3, crea GIFs animados de alta calidad y descarga videos por enlace desde redes sociales.",
        "video.tab.mp4_mp3": "MP4 a MP3",
        "video.mp3.desc": "Extrae la pista de audio de archivos de video MP4, MKV o WebM en audio MP3 nítido.",
        "video.mp3.btn_select": "Seleccionar Archivo de Video",
        "video.mp3.bitrate": "CALIDAD / BITRATE",
        "video.mp3.btn_exec": "Extraer Audio MP3",
        "video.tab.mp4_gif": "MP4 a GIF",
        "video.gif.desc": "Convierte videos o clips específicos en animaciones GIF optimizadas de alta calidad.",
        "video.gif.btn_select": "Seleccionar Archivo MP4",
        "video.gif.start_label": "TIEMPO INICIAL (S)",
        "video.gif.duration_label": "DURACIÓN (S)",
        "video.gif.fps_label": "TASA DE CUADROS (FPS)",
        "video.gif.width_label": "ANCHO (PX)",
        "video.gif.btn_exec": "Generar GIF Animado",
        "video.tab.downloader": "Descargar Videos por Enlace",
        "video.dl.desc": "Descarga videos y audios a alta velocidad desde enlaces públicos de YouTube, Twitter/X, Instagram y TikTok.",
        "video.dl.url_label": "URL DEL VIDEO",
        "video.dl.url_ph": "Pega el enlace del video aquí (ej: https://youtube.com/watch?... o https://x.com/...)",
        "video.dl.format": "FORMATO DESEADO",
        "video.dl.quality": "CALIDAD DE VIDEO",
        "video.dl.quality_audio": "CALIDAD DEL AUDIO",
        "video.dl.q_best": "Mejor Calidad",
        "video.dl.q_1080p": "1080p Full HD",
        "video.dl.q_720p": "720p HD",
        "video.dl.q_480p": "480p SD",
        "video.dl.btn_exec": "Descargar Multimedia por Enlace",

        "video.tab.converter": "Conversor de Formato",
        "video.conv.desc": "Convierte videos entre MP4, WEBM, MOV, AVI y MKV con alta calidad.",
        "video.conv.fmt_label": "FORMATO DE SALIDA",
        "video.conv.btn_exec": "Convertir Formato de Video",

        "video.tab.compressor": "Compresor de Video",
        "video.comp.desc": "Reduce el tamaño del archivo manteniendo la calidad de imagen ideal.",
        "video.comp.level_label": "NIVEL DE COMPRESIÓN",
        "video.comp.l_wa": "WhatsApp / Discord (~70%)",
        "video.comp.l_med": "Compresión Media (~50%)",
        "video.comp.l_light": "Compresión Ligera (~30%)",
        "video.comp.btn_exec": "Comprimir Video",

        "video.tab.mute": "Silenciar / Quitar Audio",
        "video.mute.desc": "Elimina la pista de audio del video sin recodificar (velocidad máxima).",
        "video.mute.btn_exec": "Silenciar Video",

        "video.tab.snap": "Capturar Foto del Video",
        "video.snap.desc": "Extrae un fotograma / foto HD del video en cualquier segundo deseado.",
        "video.snap.time_label": "SEGUNDO DEL VIDEO (S)",
        "video.snap.fmt_label": "FORMATO DE IMAGEN",
        "video.snap.btn_exec": "Capturar Imagen",

        // --- Generales ---
        "footer.rights": "Prisma Audio © 2026",
        "footer.by": "Desarrollado por Gustavo Goulart",
        "toast.done": "¡Procesamiento completado con éxito!",
        "file.none": "Ningún archivo seleccionado"
    }
};

(function () {
    function getStoredLang() {
        const saved = localStorage.getItem("prisma_lang");
        if (saved && ["pt", "en", "es"].includes(saved)) {
            return saved;
        }
        const navLang = (navigator.language || "").toLowerCase();
        if (navLang.startsWith("es")) return "es";
        if (navLang.startsWith("en")) return "en";
        return "pt";
    }

    let currentLang = getStoredLang();

    function aplicarTraducoes() {
        const dict = translations[currentLang] || translations.pt;

        document.querySelectorAll("[data-i18n]").forEach((el) => {
            const key = el.getAttribute("data-i18n");
            if (dict[key] !== undefined) {
                el.innerHTML = dict[key];
            }
        });

        document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
            const key = el.getAttribute("data-i18n-ph");
            if (dict[key] !== undefined) {
                el.placeholder = dict[key];
            }
        });

        document.querySelectorAll("[data-i18n-title]").forEach((el) => {
            const key = el.getAttribute("data-i18n-title");
            if (dict[key] !== undefined) {
                el.title = dict[key];
            }
        });

        document.querySelectorAll(".btn-lang-opt").forEach((btn) => {
            if (btn.getAttribute("data-lang") === currentLang) {
                btn.classList.add("ativo");
            } else {
                btn.classList.remove("ativo");
            }
        });

        document.documentElement.lang = currentLang === "en" ? "en" : (currentLang === "es" ? "es" : "pt-BR");
    }

    function setLanguage(lang) {
        if (!["pt", "en", "es"].includes(lang)) return;
        currentLang = lang;
        localStorage.setItem("prisma_lang", lang);
        aplicarTraducoes();
        window.dispatchEvent(new CustomEvent("languageChanged", { detail: { lang } }));
    }

    document.addEventListener("DOMContentLoaded", () => {
        aplicarTraducoes();

        document.addEventListener("click", (e) => {
            const langBtn = e.target.closest(".btn-lang-opt");
            if (langBtn) {
                const targetLang = langBtn.getAttribute("data-lang");
                if (targetLang) {
                    setLanguage(targetLang);
                }
            }
        });
    });

    window.i18n = {
        get currentLang() { return currentLang; },
        setLanguage,
        aplicarTraducoes,
        t: function(key) {
            const dict = translations[currentLang] || translations.pt;
            return dict[key] || key;
        }
    };
})();
