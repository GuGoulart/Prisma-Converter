// ── Variáveis de sessão (injetadas via data-* no body) ────────
// SEG-008: eliminados scripts inline — nenhum código Jinja2 no .js
const _bd = document.body ? document.body.dataset : {};
const origemArquivo = _bd.origem || '';
const pastaUUID = _bd.pastaUuid || '';   // camelCase: data-pasta-uuid → pastaUuid
const previewInicial = _bd.previewInicial || '';
const previewTipo = _bd.previewTipo || '';
const tabelaInicial = _bd.tabelaInicial === 'true';

// ── Limpeza de Service Worker & Cache do Navegador ─────────────
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then(registrations => {
        for (const reg of registrations) {
            reg.unregister();
        }
    });
}
if ('caches' in window) {
    caches.keys().then(keys => {
        keys.forEach(key => caches.delete(key));
    });
}

document.addEventListener("DOMContentLoaded", () => {

    // ── Tema gerenciado por theme_customizer.js ─────────────────

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
                const dict = typeof translations !== 'undefined' && typeof getCurrentLang === 'function' ? translations[getCurrentLang()] : {};
                btn.disabled = true;
                btn.innerHTML = `<span>${dict['upload.sending'] || 'Carregando...'}</span><div class="spinner"></div>`;
            }
            uploadForm.submit();
        }
    }

    uploadForm?.addEventListener("submit", () => {
        const btn = document.getElementById("btnEnviar");
        if (!btn || btn.disabled) return;
        const dict = typeof translations !== 'undefined' && typeof getCurrentLang === 'function' ? translations[getCurrentLang()] : {};
        btn.disabled = true;
        btn.innerHTML = `<span>${dict['upload.sending'] || 'Carregando...'}</span><div class="spinner"></div>`;
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

        const lang = typeof getCurrentLang === 'function' ? getCurrentLang() : 'pt';
        const dict = typeof translations !== 'undefined' ? translations[lang] || {} : {};

        // Spinner imediato
        const genMsg = (dict['preview.generating'] || 'Gerando pré-visualização {format}...').replace('{format}', destino.toUpperCase());
        viewer.innerHTML = `
            <div class="preview-loading">
                <div class="spinner-preview"></div>
                <span>${genMsg}</span>
            </div>`;
        if (sub) sub.textContent = "...";

        const ori = document.querySelector('input[name="_ori"]:checked')?.value || "retrato";

        try {

            if (destino === "pdf") {
                const url = `/preview-convert/${pastaUUID}/pdf?orientacao=${ori}`;
                const oriLabel = ori === 'paisagem' ? (dict['conv.ori.landscape'] || 'Paisagem') : (dict['conv.ori.portrait'] || 'Retrato');
                _embedComLoader(viewer, url, `PDF · ${oriLabel}`, sub);

            } else if (destino === "png" || destino === "jpg") {
                const url = `/preview-convert/${pastaUUID}/${destino}`;
                await new Promise((resolve, reject) => {
                    const img = new Image();
                    img.onload = resolve;
                    img.onerror = () => reject(new Error("Falha ao carregar imagem"));
                    img.src = url;
                });
                const rendMsg = (dict['preview.rendered'] || '{format} · renderizado').replace('{format}', destino.toUpperCase());
                viewer.innerHTML = `<img src="${url}" class="img-preview-visual" alt="Prévia ${destino.toUpperCase()}">`;
                if (sub) sub.textContent = rendMsg;

            } else if (destino === "csv" || destino === "xlsx") {
                const resp = await fetch(`/preview-tabela/${pastaUUID}/${destino}`);
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                const html = await resp.text();
                const fullMsg = (dict['preview.full_data'] || '{format} · dados completos').replace('{format}', destino.toUpperCase());
                viewer.innerHTML = `<div class="preview-scroll">${html}</div>`;
                if (sub) sub.textContent = fullMsg;

            } else if (destino === "docx") {
                const url = `/preview-convert/${pastaUUID}/pdf`;
                const visRef = (dict['preview.visual_ref'] || '{format} · ref. visual').replace('{format}', 'DOCX');
                const noticeMsg = dict['preview.docx_notice'] || 'DOCX não pode ser exibido diretamente no navegador.';
                const noticeSub = dict['preview.docx_sub'] || 'Exibindo abaixo a prévia gerada em formato PDF.';
                _embedComLoader(viewer, url, visRef, sub,
                    `<div class="preview-aviso">
                        <span>${noticeMsg}</span>
                        <span class="preview-aviso-sub">${noticeSub}</span>
                     </div>`);

            } else if (destino === "pptx" || destino === "ppt") {
                const url = `/preview-convert/${pastaUUID}/pdf`;
                const visRef = (dict['preview.visual_ref'] || '{format} · ref. visual').replace('{format}', destino.toUpperCase());
                const noticeMsg = (dict['preview.ppt_notice'] || '{format} gerado como slides por página do PDF.').replace('{format}', destino.toUpperCase());
                const noticeSub = dict['preview.ppt_sub'] || 'Exibindo abaixo o documento PDF original para referência.';
                _embedComLoader(viewer, url, visRef, sub,
                    `<div class="preview-aviso">
                        <span>${noticeMsg}</span>
                        <span class="preview-aviso-sub">${noticeSub}</span>
                     </div>`);

            } else {
                const notAvail = (dict['preview.not_available'] || 'Pré-visualização não disponível para {format}').replace('{format}', destino.toUpperCase());
                const downloadSub = dict['preview.download_to_view'] || 'Faça o download para visualizar o arquivo completo.';
                viewer.innerHTML = `
                    <div class="preview-placeholder">
                        <p class="placeholder-texto">${notAvail}</p>
                        <p class="placeholder-sub">${downloadSub}</p>
                    </div>`;
                if (sub) sub.textContent = destino.toUpperCase();
            }

        } catch (err) {
            const failTitle = dict['preview.failed'] || 'Não foi possível gerar a pré-visualização';
            viewer.innerHTML = `
                <div class="preview-erro-state">
                    <span>${failTitle}</span>
                    <span class="preview-erro-sub">${err.message || ""}</span>
                </div>`;
            if (sub) sub.textContent = "erro";
        }
    }

    // Helper: embed PDF com spinner sobreposto que some com fade
    function _embedComLoader(viewer, url, subTexto, subEl, cabecalho = "") {
        const lang = typeof getCurrentLang === 'function' ? getCurrentLang() : 'pt';
        const dict = typeof translations !== 'undefined' ? translations[lang] || {} : {};
        const loadingText = dict['upload.sending'] || 'Carregando...';

        viewer.innerHTML = `
            <div style="position:relative;width:100%;height:100%;display:flex;flex-direction:column;">
                <div class="pdf-loader-overlay" id="pdfLoaderOverlay">
                    <div class="spinner-preview"></div>
                    <span>${loadingText}</span>
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
    const converterForm = document.getElementById("converterForm");
    const btnConverter = document.getElementById("btnConverter");
    const btnOutro = document.getElementById("btnOutro");
    const progressWrap = document.getElementById("progressWrap");
    const progressBar = document.getElementById("progressBar");
    const progressLabel = document.getElementById("progressLabel");

    converterForm?.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!btnConverter || btnConverter.disabled) return;

        const lang = typeof getCurrentLang === 'function' ? getCurrentLang() : 'pt';
        const dict = typeof translations !== 'undefined' ? translations[lang] || {} : {};

        // Sincroniza orientacao do radio (se disponivel)
        const oriRadio = converterForm.querySelector("input[name='_ori']:checked");
        if (oriRadio) {
            const oriHidden = document.getElementById("orientacaoHidden");
            if (oriHidden) oriHidden.value = oriRadio.value;
        }

        // Mostrar estado de loading
        btnConverter.disabled = true;
        btnConverter.innerHTML = `<span>${dict['upload.sending'] || 'Carregando...'}</span><div class="spinner"></div>`;
        if (progressWrap) progressWrap.classList.add("ativo");
        if (progressBar) { progressBar.style.width = "5%"; progressBar.style.background = ""; }
        if (progressLabel) progressLabel.textContent = "...";

        let pollInterval = null;

        function encerrarErro(msg) {
            clearInterval(pollInterval);
            if (progressBar) { progressBar.style.width = "100%"; progressBar.style.background = "#f87171"; }
            if (progressLabel) progressLabel.textContent = msg || "Erro na conversão.";
            setTimeout(() => {
                btnConverter.disabled = false;
                btnConverter.innerHTML = `<span>${dict['conv.btn.convert'] || 'Converter e Baixar'}</span><span class="botao-arr">\u2193</span>`;
                if (progressWrap) progressWrap.classList.remove("ativo");
                if (progressBar) { progressBar.style.width = "0%"; progressBar.style.background = ""; }
            }, 3000);
        }

        function encerrarOk() {
            clearInterval(pollInterval);
            if (progressBar) progressBar.style.width = "100%";
            if (progressLabel) progressLabel.textContent = "✓";
            setTimeout(() => {
                btnConverter.disabled = false;
                btnConverter.innerHTML = `<span>${dict['conv.btn.convert'] || 'Converter e Baixar'}</span><span class="botao-arr">\u2193</span>`;
                if (progressWrap) progressWrap.classList.remove("ativo");
                if (progressBar) progressBar.style.width = "0%";
                mostrarToast(dict['toast.done'] || 'Download concluído!');
            }, 800);
        }

        try {
            // Etapa 1: Iniciar conversao assincrona com politica de autodestruição salva no modal
            const formData = new FormData(converterForm);
            const policy = (window.ThemeCustomizer && typeof window.ThemeCustomizer.getRetentionPolicy === 'function')
                ? window.ThemeCustomizer.getRetentionPolicy()
                : "15min";
            formData.set("autodestruicao", policy);

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
                    if (progressBar) progressBar.style.width = pct + "%";
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


    // ── Cronômetros de Autodestruição no Histórico em Tempo Real ──
    function iniciarCronometrosHistorico() {
        const histItems = document.querySelectorAll(".historico-item");
        if (!histItems.length) return;

        function atualizarTimers() {
            const agora = Math.floor(Date.now() / 1000);
            const lang = typeof getCurrentLang === 'function' ? getCurrentLang() : 'pt';
            const dict = typeof translations !== 'undefined' ? translations[lang] || {} : {};
            const deletedLabel = dict['conv.history.deleted'] || 'Conteúdo Apagado';

            histItems.forEach((item) => {
                const isApagado = item.getAttribute("data-apagado") === "true";
                const expiraStr = item.getAttribute("data-expires");
                if (isApagado) return;

                if (expiraStr) {
                    const expiraEm = parseInt(expiraStr, 10);
                    const restante = expiraEm - agora;

                    const rightContainer = item.querySelector(".historico-item-right");
                    const timerValSpan = item.querySelector(".hist-timer-val");

                    if (restante <= 0) {
                        item.setAttribute("data-apagado", "true");
                        const topLeft = item.querySelector(".hist-card-top-left");
                        const timerEl = item.querySelector(".hist-timer");
                        const rightContainer = item.querySelector(".historico-item-right");

                        if (topLeft) {
                            if (timerEl) timerEl.remove();
                            if (!topLeft.querySelector(".hist-timer-expired")) {
                                const expiredTag = document.createElement("span");
                                expiredTag.className = "hist-timer-expired";
                                expiredTag.innerHTML = `
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <circle cx="12" cy="12" r="10"></circle>
                                        <line x1="12" y1="8" x2="12" y2="12"></line>
                                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                                    </svg>
                                    <span>TEMPO ESGOTADO</span>`;
                                const policyTag = topLeft.querySelector(".hist-policy-tag");
                                if (policyTag && policyTag.nextSibling) {
                                    topLeft.insertBefore(expiredTag, policyTag.nextSibling);
                                } else {
                                    topLeft.appendChild(expiredTag);
                                }
                            }

                            const policy = item.getAttribute("data-policy");
                            const jobId = item.getAttribute("data-job-id");
                            if ((policy === "5min" || policy === "15min") && jobId && !topLeft.querySelector(".btn-retention-restore")) {
                                const restoreBtn = document.createElement("button");
                                restoreBtn.type = "button";
                                restoreBtn.className = "btn-retention-restore";
                                restoreBtn.title = "Restaurar Retenção";
                                restoreBtn.onclick = (e) => {
                                    e.stopPropagation();
                                    window.restaurarArquivo(jobId);
                                };
                                restoreBtn.innerHTML = "Restaurar ↺";
                                topLeft.appendChild(restoreBtn);
                            }
                        }

                        if (rightContainer) {
                            rightContainer.innerHTML = `
                                <span class="hist-apagado-badge" data-i18n="conv.history.deleted">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <polyline points="3 6 5 6 21 6"></polyline>
                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                    </svg>
                                    ${deletedLabel}
                                </span>`;
                        }
                    } else if (timerValSpan) {
                        const m = Math.floor(restante / 60);
                        const s = restante % 60;
                        timerValSpan.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
                    }
                }
            });
        }

        atualizarTimers();
        setInterval(atualizarTimers, 1000);
    }

    iniciarCronometrosHistorico();

    // ── Função de Restauração de Arquivo em Tempo Real ─────────
    window.restaurarArquivo = async function (jobId) {
        if (!jobId) return;
        try {
            const resp = await fetch("/api/historico/restaurar/" + jobId, {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            const data = await resp.json();
            const lang = typeof getCurrentLang === 'function' ? getCurrentLang() : 'pt';
            const dict = typeof translations !== 'undefined' ? translations[lang] || {} : {};

            if (!resp.ok || data.erro) {
                mostrarToast(data.erro || "Não foi possível restaurar o arquivo.");
                return;
            }

            // Atualizar elementos do histórico na DOM
            const items = document.querySelectorAll(`.historico-item[data-job-id="${jobId}"], #hist-card-${jobId}`);
            items.forEach((el) => {
                el.setAttribute("data-expires", data.expira_em);
                el.setAttribute("data-apagado", "false");
                const timerVal = el.querySelector(".hist-timer-val");
                if (timerVal) {
                    const restante = Math.max(0, data.expira_em - Math.floor(Date.now() / 1000));
                    const m = Math.floor(restante / 60);
                    const s = restante % 60;
                    timerVal.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
                }
            });

            const msg = dict['conv.history.restoreToast'] || data.mensagem || "Arquivo restaurado com sucesso!";
            mostrarToast(msg);
        } catch (err) {
            console.error("Erro ao restaurar arquivo:", err);
            mostrarToast("Erro de conexão ao restaurar arquivo.");
        }
    };

    // ── Relógio no rodapé ─────────────────────────────────────

    // ── Painel de ações do histórico ──────────────────────────
    function atualizarEstadoDownloadLote() {
        const downloadAllBtn = document.getElementById("downloadAllHistory");
        if (!downloadAllBtn) return;
        const histItems = document.querySelectorAll(".historico-item");
        let temAtivo = false;
        histItems.forEach((item) => {
            const isApagado = item.getAttribute("data-apagado") === "true";
            const policy = item.getAttribute("data-policy");
            if (!isApagado && (policy === "5min" || policy === "15min")) {
                temAtivo = true;
            }
        });
        if (temAtivo) {
            downloadAllBtn.classList.remove("btn-disabled");
            downloadAllBtn.disabled = false;
            downloadAllBtn.title = "Baixar todos (ZIP)";
        } else {
            downloadAllBtn.classList.add("btn-disabled");
            downloadAllBtn.disabled = true;
            downloadAllBtn.title = "Nenhum arquivo ativo disponível para download em lote";
        }
    }

    atualizarEstadoDownloadLote();

    document.getElementById("downloadAllHistory")?.addEventListener("click", async (event) => {
        const btn = document.getElementById("downloadAllHistory");
        if (btn?.classList.contains("btn-disabled") || btn?.disabled) {
            event?.preventDefault();
            mostrarToast("Nenhum arquivo ativo disponível para download em lote.");
            return;
        }
        try {
            const response = await fetch("/api/historico/zip-todos");
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.erro || "Não há arquivos de 5 ou 15 minutos disponíveis para o ZIP.");
            }
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = "prisma_lote_arquivos.zip";
            link.click();
            URL.revokeObjectURL(url);
            mostrarToast("ZIP pronto para download.");
        } catch (error) { mostrarToast(error.message || "Não foi possível gerar o ZIP."); }
    });

    const destroyModal = document.getElementById("destroyHistoryModal");
    function fecharModalDestruir() {
        destroyModal?.classList.remove("open");
        destroyModal?.setAttribute("aria-hidden", "true");
    }
    document.getElementById("destroyAllHistory")?.addEventListener("click", () => {
        destroyModal?.classList.add("open");
        destroyModal?.setAttribute("aria-hidden", "false");
    });
    document.getElementById("closeDestroyModal")?.addEventListener("click", fecharModalDestruir);
    document.getElementById("cancelDestroyHistory")?.addEventListener("click", fecharModalDestruir);
    destroyModal?.addEventListener("click", (event) => { if (event.target === destroyModal) fecharModalDestruir(); });
    document.getElementById("confirmDestroyHistory")?.addEventListener("click", async () => {
        try {
            const response = await fetch("/api/historico/destruir-tudo", { method: "POST" });
            const data = await response.json();
            if (!response.ok || data.erro) throw new Error(data.erro || "Falha ao destruir os arquivos.");
            fecharModalDestruir();

            // Atualiza o estado visual das opções de download imediatamente
            const histItems = document.querySelectorAll(".historico-item");
            histItems.forEach((item) => item.setAttribute("data-apagado", "true"));
            atualizarEstadoDownloadLote();

            mostrarToast(data.mensagem || "Arquivos destruídos.");
            window.setTimeout(() => window.location.reload(), 500);
        } catch (error) { mostrarToast(error.message || "Não foi possível destruir os arquivos."); }
    });

    const retentionRoot = document.getElementById("historyRetention");
    function atualizarRetencaoSelecionada(policy) {
        retentionRoot?.querySelectorAll(".btn-ret-opt").forEach((button) => button.classList.toggle("active", button.dataset.policy === policy));
    }
    atualizarRetencaoSelecionada(document.body.dataset.retentionPolicy || "15min");
    retentionRoot?.addEventListener("click", async (event) => {
        const button = event.target.closest(".btn-ret-opt");
        if (!button) return;
        const politica = button.dataset.policy;
        try {
            const response = await fetch("/api/historico/set-politica", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ politica }) });
            const data = await response.json();
            if (!response.ok || data.erro) throw new Error(data.erro || "Falha ao salvar a preferência.");
            window.ThemeCustomizer?.setRetentionPolicy?.(politica);
            atualizarRetencaoSelecionada(politica);
            mostrarToast("Preferência de retenção atualizada.");
        } catch (error) { mostrarToast(error.message || "Não foi possível salvar a preferência."); }
    });

    const secureWipeToggle = document.getElementById("secureWipeToggle");
    if (secureWipeToggle) {
        secureWipeToggle.checked = document.body.dataset.secureWipe !== "false";
        secureWipeToggle.addEventListener("change", async () => {
            const modo_seguro = secureWipeToggle.checked;
            try {
                const response = await fetch("/api/historico/set-seguranca", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ modo_seguro }) });
                if (!response.ok) throw new Error("Falha ao salvar a preferência de segurança.");
                mostrarToast(modo_seguro ? "Eliminação segura ativada." : "Eliminação segura desativada.");
            } catch (error) {
                secureWipeToggle.checked = !modo_seguro;
                mostrarToast(error.message || "Não foi possível salvar a preferência.");
            }
        });
    }

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

    // ── Suporte a Instalação do App (PWA Prompt / Executável Desktop) ──
    document.querySelectorAll("#btnInstallApp").forEach(btn => {
        btn.addEventListener("click", (e) => {
            if (window.deferredPwaPrompt) {
                e.preventDefault();
                window.deferredPwaPrompt.prompt();
                window.deferredPwaPrompt.userChoice.then((choice) => {
                    if (choice.outcome !== "accepted") {
                        window.location.href = "/download-app";
                    }
                    window.deferredPwaPrompt = null;
                });
            }
        });
    });

}); // fim DOMContentLoaded

// Captura evento de instalação PWA
window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    window.deferredPwaPrompt = e;
    document.querySelectorAll("#btnInstallApp").forEach(btn => {
        btn.classList.add("pwa-ready");
    });
});


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
