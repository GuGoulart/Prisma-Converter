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
                const planilha = ["xlsx", "xls", "csv"].includes(origemArquivo);
                orientacaoWrap.classList.toggle("visivel", planilha && destino === "pdf");
            }

            if (pastaUUID) atualizarPreview(destino);
        });
    });

    // Orientação no carregamento inicial
    if (pastaUUID && origemArquivo && orientacaoWrap) {
        const primDest = document.querySelector('input[name="destino"]:checked')?.value;
        if (["xlsx", "xls", "csv"].includes(origemArquivo) && primDest === "pdf") {
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


    // ── Form de conversão — progresso + cookie poll ───────────

    document.getElementById("converterForm")?.addEventListener("submit", () => {
        const btn = document.getElementById("btnConverter");
        const btnOutro = document.getElementById("btnOutro");
        const progressWrap = document.getElementById("progressWrap");
        const progressBar = document.getElementById("progressBar");
        const progressLabel = document.getElementById("progressLabel");
        if (!btn) return;

        const token = Math.random().toString(36).slice(2) + Date.now();
        let ti = document.querySelector("input[name='downloadToken']");
        if (!ti) {
            ti = document.createElement("input");
            ti.type = "hidden";
            ti.name = "downloadToken";
            document.getElementById("converterForm").appendChild(ti);
        }
        ti.value = token;

        btn.disabled = true;
        btn.innerHTML = `<span>Processando...</span><div class="spinner"></div>`;
        progressWrap.classList.add("ativo");
        progressLabel.textContent = "0%";

        const fases = [
            { pct: 15, label: "Lendo arquivo...", delay: 300 },
            { pct: 35, label: "Convertendo...", delay: 1200 },
            { pct: 60, label: "Processando...", delay: 2800 },
            { pct: 80, label: "Finalizando...", delay: 5000 },
            { pct: 88, label: "Quase pronto...", delay: 8000 },
        ];
        fases.forEach(({ pct, label, delay }) => {
            setTimeout(() => {
                if (btn.disabled) {
                    progressBar.style.width = pct + "%";
                    progressLabel.textContent = label;
                }
            }, delay);
        });

        const poll = setInterval(() => {
            const concluido = document.cookie
                .split(";")
                .some(c => c.trim() === `downloadToken=${token}`);
            if (concluido) {
                clearInterval(poll);
                document.cookie = `downloadToken=${token}; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
                progressBar.style.width = "100%";
                progressLabel.textContent = "Concluído!";
                setTimeout(() => {
                    btn.disabled = false;
                    btn.innerHTML = `<span>Converter e baixar</span><span class="botao-arr">↓</span>`;
                    progressWrap.classList.remove("ativo");
                    progressBar.style.width = "0%";
                    if (btnOutro) btnOutro.style.display = "flex";
                    mostrarToast("Download concluído!");
                }, 600);
            }
        }, 400);

        setTimeout(() => {
            clearInterval(poll);
            if (btn.disabled) {
                btn.disabled = false;
                btn.innerHTML = `<span>Converter e baixar</span><span class="botao-arr">↓</span>`;
                progressWrap.classList.remove("ativo");
            }
        }, 120_000);
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