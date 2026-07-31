// ── Variáveis de sessão (injetadas via data-* no body) ────────
// SEG-008: eliminados scripts inline — nenhum código Jinja2 no .js
const _bd = document.body ? document.body.dataset : {};
const origemArquivo = _bd.origem         || '';
const pastaUUID     = _bd.pastaUuid      || '';   // camelCase: data-pasta-uuid → pastaUuid
const previewInicial = _bd.previewInicial || '';
const previewTipo    = _bd.previewTipo    || '';
const tabelaInicial  = _bd.tabelaInicial  === 'true';

// ── Service Worker ────────────────────────────────────────────
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('[SW] registrado', reg.scope))
            .catch(err => console.error('[SW] erro', err));
    });
}

document.addEventListener("DOMContentLoaded", () => {

    // ── Tema Claro / Escuro ───────────────────────────────────
    const themeToggleBtn = document.getElementById("themeToggle");
    const currentTheme = localStorage.getItem("theme") || "dark";

    if (currentTheme === "light") {
        document.documentElement.setAttribute("data-theme", "light");
    }

    themeToggleBtn?.addEventListener("click", () => {
        let theme = document.documentElement.getAttribute("data-theme");
        if (theme === "light") {
            document.documentElement.removeAttribute("data-theme");
            localStorage.setItem("theme", "dark");
        } else {
            document.documentElement.setAttribute("data-theme", "light");
            localStorage.setItem("theme", "light");
        }
    });

    // ── Upload box ────────────────────────────────────────────

    const uploadBox = document.getElementById("uploadBox");
    const inputFile = document.getElementById("arquivo");
    const uploadTitulo = document.getElementById("uploadTitulo");
    const uploadDesc = document.getElementById("uploadDesc");
    const uploadIcone = document.getElementById("uploadIcone");
    const uploadForm = document.getElementById("uploadForm");

    uploadBox?.addEventListener("click", (e) => {
        if (e.target.tagName !== "INPUT") inputFile.click();
    });

    inputFile?.addEventListener("change", () => atualizarUploadUI(false));

    function atualizarUploadUI(autoSubmit = false) {
        if (!inputFile?.files?.length) return;
        const f = inputFile.files[0];
        const ext = f.name.split(".").pop().toLowerCase();
        const tam = formatarTamanho(f.size);
        uploadIcone.innerHTML = `<span style="font-family:var(--mono);font-size:13px;font-weight:700;color:var(--accent);letter-spacing:.1em;">.${ext}</span>`;
        uploadTitulo.textContent = f.name;
        uploadDesc.textContent = `${ext.toUpperCase()} · ${tam}`;
        uploadBox.style.borderColor = "var(--accent)";
        uploadBox.querySelectorAll(".corner").forEach(c => {
            c.style.borderColor = "var(--accent)";
            c.style.opacity = "1";
        });
        if (autoSubmit && uploadForm) {
            const btn = document.getElementById("btnEnviar");
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = `<span>Enviando...</span><div class="spinner"></div>`;
            }
            uploadForm.submit();
        }
    }

    uploadForm?.addEventListener("submit", () => {
        const btn = document.getElementById("btnEnviar");
        if (!btn || btn.disabled) return;
        btn.disabled = true;
        btn.innerHTML = `<span>Enviando...</span><div class="spinner"></div>`;
    });


    // ── Drag & Drop ───────────────────────────────────────────

    ["dragenter", "dragover"].forEach(ev =>
        uploadBox?.addEventListener(ev, (e) => {
            e.preventDefault();
            uploadBox.classList.add("drag-over");
        })
    );
    uploadBox?.addEventListener("dragleave", (e) => {
        e.preventDefault();
        uploadBox.classList.remove("drag-over");
    });
    uploadBox?.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadBox.classList.remove("drag-over");
        inputFile.files = e.dataTransfer.files;
        atualizarUploadUI(true);
    });


    // ── Orientação ────────────────────────────────────────────

    const orientacaoWrap = document.getElementById("orientacaoWrap");
    const orientacaoHidden = document.getElementById("orientacaoHidden");

    document.querySelectorAll('input[name="_ori"]').forEach(radio => {
        radio.addEventListener("change", (e) => {
            if (orientacaoHidden) orientacaoHidden.value = e.target.value;
            const dest = document.querySelector('input[name="destino"]:checked')?.value;
            if (dest === "pdf") atualizarPreview("pdf");
        });
    });


    // ── Seleção de destino → atualiza preview ─────────────────

    document.querySelectorAll('input[name="destino"]').forEach(radio => {
        radio.addEventListener("change", (e) => {
            const destino = e.target.value;

            // Mostra/oculta painel de orientação
            if (orientacaoWrap) {
                // UX-002: json também suporta orientação de PDF
                const planilha = ["xlsx", "xls", "csv", "json"].includes(origemArquivo);
                orientacaoWrap.classList.toggle("visivel", planilha && destino === "pdf");
            }

            if (pastaUUID) atualizarPreview(destino);
        });
    });

    // Orientação no carregamento inicial
    if (pastaUUID && origemArquivo && orientacaoWrap) {
        const primDest = document.querySelector('input[name="destino"]:checked')?.value;
        // UX-002: inclui json
        if (["xlsx", "xls", "csv", "json"].includes(origemArquivo) && primDest === "pdf") {
            orientacaoWrap.classList.add("visivel");
        }
    }


    // ── Preview dinâmico ──────────────────────────────────────

    async function atualizarPreview(destino) {
        if (!pastaUUID) return;
        const viewer = document.getElementById("previewViewer");
        const sub = document.getElementById("previewSub");
        if (!viewer) return;

        // Spinner imediato
        viewer.innerHTML = `
            <div class="preview-loading">
                <div class="spinner-preview"></div>
                <span>Gerando prévia ${destino.toUpperCase()}...</span>
            </div>`;
        if (sub) sub.textContent = "Gerando...";

        const ori = document.querySelector('input[name="_ori"]:checked')?.value || "retrato";

        try {

            if (destino === "pdf") {
                const url = `/preview-convert/${pastaUUID}/pdf?orientacao=${ori}`;
                _embedComLoader(viewer, url, `PDF · ${ori}`, sub);

            } else if (destino === "png" || destino === "jpg") {
                const url = `/preview-convert/${pastaUUID}/${destino}`;
                await new Promise((resolve, reject) => {
                    const img = new Image();
                    img.onload = resolve;
                    img.onerror = () => reject(new Error("Falha ao carregar imagem"));
                    img.src = url;
                });
                viewer.innerHTML = `<img src="${url}" class="img-preview-visual" alt="Prévia ${destino.toUpperCase()}">`;
                if (sub) sub.textContent = `${destino.toUpperCase()} · renderizado`;

            } else if (destino === "csv" || destino === "xlsx") {
                const resp = await fetch(`/preview-tabela/${pastaUUID}/${destino}`);
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                const html = await resp.text();
                viewer.innerHTML = `<div class="preview-scroll">${html}</div>`;
                if (sub) sub.textContent = `${destino.toUpperCase()} · dados completos`;

            } else if (destino === "docx") {
                const url = `/preview-convert/${pastaUUID}/pdf`;
                _embedComLoader(viewer, url, "DOCX · ref. visual", sub,
                    `<div class="preview-aviso">
                        <span>DOCX não pode ser pré-visualizado no browser.</span>
                        <span class="preview-aviso-sub">Abaixo: aparência como PDF</span>
                     </div>`);

            } else if (destino === "pptx" || destino === "ppt") {
                const url = `/preview-convert/${pastaUUID}/pdf`;
                _embedComLoader(viewer, url, `${destino.toUpperCase()} · ref. visual`, sub,
                    `<div class="preview-aviso">
                        <span>${destino.toUpperCase()} gerado como slides por página do PDF.</span>
                        <span class="preview-aviso-sub">Abaixo: PDF original para referência</span>
                     </div>`);

            } else {
                viewer.innerHTML = `
                    <div class="preview-placeholder">
                        <p class="placeholder-texto">Prévia não disponível para ${destino.toUpperCase()}</p>
                        <p class="placeholder-sub">Faça o download para visualizar.</p>
                    </div>`;
                if (sub) sub.textContent = destino.toUpperCase();
            }

        } catch (err) {
            viewer.innerHTML = `
                <div class="preview-erro-state">
                    <span>Não foi possível gerar a prévia</span>
                    <span class="preview-erro-sub">${err.message || "Tente fazer o download"}</span>
                </div>`;
            if (sub) sub.textContent = "erro";
        }
    }

    // Helper: embed PDF com spinner sobreposto que some com fade
    function _embedComLoader(viewer, url, subTexto, subEl, cabecalho = "") {
        viewer.innerHTML = `
            <div style="position:relative;width:100%;height:100%;display:flex;flex-direction:column;">
                <div class="pdf-loader-overlay" id="pdfLoaderOverlay">
                    <div class="spinner-preview"></div>
                    <span>Carregando...</span>
                </div>
                ${cabecalho}
                <embed src="${url}#toolbar=0&navpanes=0&scrollbar=1"
                       type="application/pdf"
                       class="pdf-embed"
                       style="flex:1;min-height:200px;">
            </div>`;
        if (subEl) subEl.textContent = subTexto;

        setTimeout(() => {
            const overlay = document.getElementById("pdfLoaderOverlay");
            if (overlay) {
                overlay.style.opacity = "0";
                setTimeout(() => overlay?.remove(), 300);
            }
        }, 1500);
    }


    // -- Form de conversao -- Async API com progresso em tempo real -----------
    // Fluxo:
    //  1. Intercepta submit do #converterForm
    //  2. POST /api/converter/async -> recebe job_id
    //  3. Polling /api/converter/status/<job_id> a cada 800ms
    //  4. Quando concluido=true -> redirect para /api/converter/download/<job_id>
    // Fallback: se fetch falhar completamente, o submit normal e acionado.

    const converterForm = document.getElementById("converterForm");
    const btnConverter  = document.getElementById("btnConverter");
    const btnOutro      = document.getElementById("btnOutro");
    const progressWrap  = document.getElementById("progressWrap");
    const progressBar   = document.getElementById("progressBar");
    const progressLabel = document.getElementById("progressLabel");

    converterForm?.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!btnConverter || btnConverter.disabled) return;

        // Sincroniza orientacao do radio (se disponivel)
        const oriRadio = converterForm.querySelector("input[name='_ori']:checked");
        if (oriRadio) {
            const oriHidden = document.getElementById("orientacaoHidden");
            if (oriHidden) oriHidden.value = oriRadio.value;
        }

        // Mostrar estado de loading
        btnConverter.disabled = true;
        btnConverter.innerHTML = '<span>Processando...</span><div class="spinner"></div>';
        if (progressWrap)  progressWrap.classList.add("ativo");
        if (progressBar)   { progressBar.style.width = "5%"; progressBar.style.background = ""; }
        if (progressLabel) progressLabel.textContent = "Iniciando...";

        let pollInterval = null;

        function encerrarErro(msg) {
            clearInterval(pollInterval);
            if (progressBar)  { progressBar.style.width = "100%"; progressBar.style.background = "#f87171"; }
            if (progressLabel) progressLabel.textContent = msg || "Erro na conversao.";
            setTimeout(() => {
                btnConverter.disabled = false;
                btnConverter.innerHTML = '<span>Converter e baixar</span><span class="botao-arr">\u2193</span>';
                if (progressWrap) progressWrap.classList.remove("ativo");
                if (progressBar)  { progressBar.style.width = "0%"; progressBar.style.background = ""; }
            }, 3000);
        }

        function encerrarOk() {
            clearInterval(pollInterval);
            if (progressBar)   progressBar.style.width = "100%";
            if (progressLabel) progressLabel.textContent = "Concluido!";
            setTimeout(() => {
                btnConverter.disabled = false;
                btnConverter.innerHTML = '<span>Converter e baixar</span><span class="botao-arr">\u2193</span>';
                if (progressWrap) progressWrap.classList.remove("ativo");
                if (progressBar)  progressBar.style.width = "0%";
                if (btnOutro) btnOutro.style.display = "flex";
                mostrarToast("Download concluido!");
            }, 800);
        }

        try {
            // Etapa 1: Iniciar conversao assincrona
            const formData = new FormData(converterForm);
            const resp = await fetch("/api/converter/async", { method: "POST", body: formData });

            if (!resp.ok) {
                const errData = await resp.json().catch(() => ({}));
                encerrarErro(errData.erro || "Erro " + resp.status);
                return;
            }

            const data = await resp.json();
            if (data.erro || !data.job_id) {
                encerrarErro(data.erro || "Erro ao iniciar conversao.");
                return;
            }

            const jobId = data.job_id;
            if (progressLabel) progressLabel.textContent = "Aguardando processamento...";

            // Etapa 2: Polling do status
            let tentativas = 0;
            const MAX_TENTATIVAS = 180; // 180 x 800ms = 144s

            pollInterval = setInterval(async () => {
                tentativas++;
                if (tentativas > MAX_TENTATIVAS) {
                    encerrarErro("Tempo excedido. Tente com um arquivo menor.");
                    return;
                }

                try {
                    const sr = await fetch("/api/converter/status/" + jobId);
                    if (!sr.ok) return; // Ignora falhas transitorias

                    const status = await sr.json();
                    if (status.erro) { encerrarErro(status.erro); return; }

                    // Atualizar barra de progresso
                    const pct = Math.max(5, Math.min(99, status.percent || 5));
                    if (progressBar)   progressBar.style.width = pct + "%";
                    if (progressLabel) progressLabel.textContent = status.status || "Convertendo...";

                    // Conversao concluida!
                    if (status.concluido && status.download_url) {
                        encerrarOk();
                        window.location.href = status.download_url; // auto-download
                    }
                } catch (netErr) {
                    console.warn("[converter] Erro no poll de status:", netErr);
                }
            }, 800);

        } catch (fetchErr) {
            // Fallback sincrono caso o fetch falhe completamente
            console.warn("[converter] fetch falhou, usando submit sincrono:", fetchErr);
            clearInterval(pollInterval);
            btnConverter.disabled = false;
            btnConverter.innerHTML = '<span>Converter e baixar</span><span class="botao-arr">\u2193</span>';
            if (progressWrap) progressWrap.classList.remove("ativo");
            converterForm.submit();
        }
    });



    // ── Atalhos de teclado ────────────────────────────────────

    document.addEventListener("keydown", (e) => {
        const tag = document.activeElement?.tagName;
        const emInput = ["INPUT", "TEXTAREA", "SELECT"].includes(tag);

        if (e.key.toLowerCase() === "k" && !e.ctrlKey && !e.metaKey && !emInput)
            inputFile?.click();

        if (e.key === "Enter" && !e.ctrlKey && !e.metaKey && !emInput && tag !== "BUTTON") {
            const btn = document.getElementById("btnConverter");
            if (btn && !btn.disabled) btn.click();
        }

        if (e.key === "Escape") fecharDrawer();
    });


    // ── Relógio no rodapé ─────────────────────────────────────

    const relogio = document.getElementById("relogio");
    if (relogio) {
        const tick = () => relogio.textContent = new Date().toLocaleTimeString("pt-BR", {
            hour: "2-digit", minute: "2-digit", second: "2-digit"
        });
        tick();
        setInterval(tick, 1000);
    }


    // ── Drawer mobile (toggle com hambúrguer) ─────────────────

    const menuBtn = document.getElementById("menuBtn");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("drawerOverlay");

    function toggleDrawer() {
        const aberta = sidebar?.classList.contains("aberta");
        if (aberta) {
            fecharDrawer();
        } else {
            abrirDrawer();
        }
    }

    function abrirDrawer() {
        sidebar?.classList.add("aberta");
        overlay?.classList.add("ativo");
        menuBtn?.classList.add("ativo");
        document.body.style.overflow = "hidden";
    }

    function fecharDrawer() {
        sidebar?.classList.remove("aberta");
        overlay?.classList.remove("ativo");
        menuBtn?.classList.remove("ativo");
        document.body.style.overflow = "";
    }

    menuBtn?.addEventListener("click", toggleDrawer);
    overlay?.addEventListener("click", fecharDrawer);

}); // fim DOMContentLoaded


// ── Funções globais ───────────────────────────────────────────

function mostrarToast(msg) {
    const t = document.getElementById("toast");
    if (!t) return;
    t.querySelector(".toast-msg").textContent = msg;
    t.classList.add("visivel");
    setTimeout(() => t.classList.remove("visivel"), 3000);
}

function formatarTamanho(b) {
    if (b < 1024) return b + " B";
    if (b < 1_048_576) return (b / 1024).toFixed(1) + " KB";
    return (b / 1_048_576).toFixed(1) + " MB";
}