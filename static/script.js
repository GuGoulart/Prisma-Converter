document.addEventListener("DOMContentLoaded", () => {

    const uploadBox    = document.getElementById("uploadBox");
    const inputFile    = document.getElementById("arquivo");
    const uploadIcone  = document.getElementById("uploadIcone");
    const uploadTitulo = document.getElementById("uploadTitulo");
    const uploadDesc   = document.getElementById("uploadDesc");
    const uploadForm   = document.getElementById("uploadForm");

    // ─────────────────────────────
    // Upload box — clique
    // ─────────────────────────────

    uploadBox?.addEventListener("click", (e) => {
        if (e.target.tagName !== "INPUT") inputFile.click();
    });

    inputFile?.addEventListener("change", () => atualizarUpload(false));

    function atualizarUpload(autoSubmit = false) {
        if (!inputFile.files.length) return;

        const f   = inputFile.files[0];
        const ext = f.name.split(".").pop().toLowerCase();
        const tam = formatarTamanho(f.size);

        uploadIcone.innerHTML = `
            <span style="font-family:var(--mono);font-size:13px;font-weight:700;
                         color:var(--accent);letter-spacing:.1em;">.${ext}</span>`;

        uploadTitulo.textContent = f.name;
        uploadDesc.textContent   = `${ext.toUpperCase()} · ${tam}${autoSubmit ? " · enviando..." : " · pronto"}`;

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

    // ─────────────────────────────
    // Drag & Drop
    // ─────────────────────────────

    ["dragenter", "dragover"].forEach(evt => {
        uploadBox?.addEventListener(evt, (e) => {
            e.preventDefault();
            uploadBox.classList.add("drag-over");
        });
    });

    uploadBox?.addEventListener("dragleave", (e) => {
        e.preventDefault();
        uploadBox.classList.remove("drag-over");
    });

    uploadBox?.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadBox.classList.remove("drag-over");
        inputFile.files = e.dataTransfer.files;
        atualizarUpload(true);
    });

    // ─────────────────────────────
    // Atalhos de teclado
    // ─────────────────────────────

    document.addEventListener("keydown", (e) => {
        const tag = document.activeElement?.tagName;
        const emInput = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";

        if (e.key.toLowerCase() === "k" && !e.ctrlKey && !e.metaKey && !emInput) {
            inputFile?.click();
        }

        if (e.key === "Enter" && !e.ctrlKey && !e.metaKey && !emInput && tag !== "BUTTON") {
            const btnConverter = document.getElementById("btnConverter");
            if (btnConverter && !btnConverter.disabled) btnConverter.click();
        }

        if (e.key === "Escape") fecharDrawer();
    });

    // ─────────────────────────────
    // Form upload — loading
    // ─────────────────────────────

    uploadForm?.addEventListener("submit", () => {
        const btn = document.getElementById("btnEnviar");
        if (!btn || btn.disabled) return;
        btn.disabled = true;
        btn.innerHTML = `<span>Enviando...</span><div class="spinner"></div>`;
    });

    // ─────────────────────────────
    // Form conversão — progresso + cookie
    // ─────────────────────────────

    document.getElementById("converterForm")?.addEventListener("submit", () => {
        const btn          = document.getElementById("btnConverter");
        const btnOutro     = document.getElementById("btnOutro");
        const progressWrap = document.getElementById("progressWrap");
        const progressBar  = document.getElementById("progressBar");
        const progressLabel = document.getElementById("progressLabel");

        if (!btn) return;

        const token = Math.random().toString(36).slice(2) + Date.now();

        let tokenInput = document.querySelector("input[name='downloadToken']");
        if (!tokenInput) {
            tokenInput = document.createElement("input");
            tokenInput.type = "hidden";
            tokenInput.name = "downloadToken";
            document.getElementById("converterForm").appendChild(tokenInput);
        }
        tokenInput.value = token;

        btn.disabled = true;
        btn.innerHTML = `<span>Processando...</span><div class="spinner"></div>`;

        progressWrap.classList.add("ativo");
        progressLabel.textContent = "0%";

        const fases = [
            { pct: 15, label: "Lendo arquivo...",  delay: 300  },
            { pct: 35, label: "Convertendo...",    delay: 1200 },
            { pct: 60, label: "Processando...",    delay: 2800 },
            { pct: 80, label: "Finalizando...",    delay: 5000 },
            { pct: 88, label: "Quase pronto...",   delay: 8000 },
        ];

        fases.forEach(({ pct, label, delay }) => {
            setTimeout(() => {
                if (btn.disabled) {
                    progressBar.style.width   = pct + "%";
                    progressLabel.textContent = label;
                }
            }, delay);
        });

        const poll = setInterval(() => {
            const encontrou = document.cookie
                .split(";")
                .some(c => c.trim() === `downloadToken=${token}`);

            if (encontrou) {
                clearInterval(poll);
                document.cookie = `downloadToken=${token}; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;

                progressBar.style.width   = "100%";
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

    // ─────────────────────────────
    // Relógio
    // ─────────────────────────────

    const relogio = document.getElementById("relogio");
    if (relogio) {
        const tick = () => {
            relogio.textContent = new Date().toLocaleTimeString("pt-BR", {
                hour: "2-digit", minute: "2-digit", second: "2-digit"
            });
        };
        tick();
        setInterval(tick, 1000);
    }

    // ─────────────────────────────
    // Drawer mobile
    // ─────────────────────────────

    const menuBtn    = document.getElementById("menuBtn");
    const sidebar    = document.getElementById("sidebar");
    const overlay    = document.getElementById("drawerOverlay");
    const btnFechar  = document.getElementById("btnFecharSidebar");

    function abrirDrawer() {
        sidebar?.classList.add("aberta");
        overlay?.classList.add("ativo");
        document.body.style.overflow = "hidden";
    }

    function fecharDrawer() {
        sidebar?.classList.remove("aberta");
        overlay?.classList.remove("ativo");
        document.body.style.overflow = "";
    }

    menuBtn?.addEventListener("click", abrirDrawer);
    btnFechar?.addEventListener("click", fecharDrawer);
    overlay?.addEventListener("click", fecharDrawer);

});

// ─────────────────────────────
// Toast
// ─────────────────────────────

function mostrarToast(msg) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.querySelector(".toast-msg").textContent = msg;
    toast.classList.add("visivel");
    setTimeout(() => toast.classList.remove("visivel"), 3000);
}

// ─────────────────────────────
// Utilitários
// ─────────────────────────────

function formatarTamanho(bytes) {
    if (bytes < 1024)       return bytes + " B";
    if (bytes < 1_048_576)  return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1_048_576).toFixed(1) + " MB";
}