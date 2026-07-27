/**
 * pdf_tools.js — Script externo para a página de Ferramentas Avançadas
 * SEG-008: Migrado do inline <script> do pdf_tools.html para eliminar unsafe-inline no CSP
 */

// ── Service Worker ────────────────────────────────────────────
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('[SW] registrado', reg.scope))
            .catch(err => console.error('[SW] erro', err));
    });
}

document.addEventListener('DOMContentLoaded', () => {

    // ── Tema Claro / Escuro ───────────────────────────────────
    const themeToggle = document.getElementById('themeToggle');
    const root = document.documentElement;
    const isLight = localStorage.getItem('theme') === 'light';

    if (isLight) root.setAttribute('data-theme', 'light');

    themeToggle?.addEventListener('click', () => {
        const light = root.getAttribute('data-theme') === 'light';
        if (light) {
            root.removeAttribute('data-theme');
            localStorage.setItem('theme', 'dark');
        } else {
            root.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    });

    // ── Drawer mobile ─────────────────────────────────────────
    const menuBtn = document.getElementById('menuBtn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('drawerOverlay');

    menuBtn?.addEventListener('click', () => {
        sidebar?.classList.toggle('aberta');
        overlay?.classList.toggle('ativo');
        menuBtn?.classList.toggle('ativo');
        document.body.style.overflow = sidebar?.classList.contains('aberta') ? 'hidden' : '';
    });

    overlay?.addEventListener('click', () => {
        sidebar?.classList.remove('aberta');
        overlay?.classList.remove('ativo');
        menuBtn?.classList.remove('ativo');
        document.body.style.overflow = '';
    });

    // ── Auto-ocultar mensagem de erro após 5s ─────────────────
    setTimeout(() => {
        const erroBox = document.querySelector('.erro-box');
        if (erroBox) {
            erroBox.style.transition = 'opacity 0.3s';
            erroBox.style.opacity = '0';
            setTimeout(() => erroBox.style.display = 'none', 300);
        }
    }, 5000);

    // ── Mesclar PDFs: acumular arquivos em DataTransfer ───────
    const dt = new DataTransfer();
    const mergeInput = document.getElementById('mergeInput');
    const mergeListContainer = document.getElementById('mergeListContainer');
    const mergeEmptyMsg = document.getElementById('mergeEmptyMsg');

    mergeInput?.addEventListener('change', function () {
        for (const file of this.files) { dt.items.add(file); }
        this.files = dt.files;
        mergeListContainer?.querySelectorAll('.merge-item').forEach(o => o.remove());
        if (dt.files.length > 0 && mergeEmptyMsg) mergeEmptyMsg.style.display = 'none';
        for (const file of dt.files) {
            const div = document.createElement('div');
            div.className = 'merge-item';
            div.textContent = 'P ' + file.name;
            div.style.cssText = 'font-size:12px;color:var(--text);background:var(--surface);padding:4px 8px;border-radius:4px;';
            mergeListContainer?.appendChild(div);
        }
    });

    // ── Dividir PDF: modo de divisão ──────────────────────────
    const splitModo = document.getElementById('splitModo');
    const splitParametro = document.getElementById('splitParametro');
    const splitInfo = document.getElementById('splitInfo');

    if (splitModo && splitParametro && splitInfo) {
        splitModo.addEventListener('change', (e) => {
            const v = e.target.value;
            if (v === 'individual') {
                splitParametro.style.display = 'none';
                splitParametro.required = false;
                splitInfo.textContent = 'Cria um arquivo separado para cada página do seu PDF original.';
            } else if (v === 'fixo') {
                splitParametro.style.display = 'block';
                splitParametro.placeholder = 'Cortar a cada quantas páginas? Ex: 2';
                splitParametro.required = true;
                splitInfo.textContent = 'Agrupa o PDF em blocos do tamanho que você escolher.';
            } else if (v === 'custom') {
                splitParametro.style.display = 'block';
                splitParametro.placeholder = 'Páginas específicas. Ex: 1-2, 5, 7-10';
                splitParametro.required = true;
                splitInfo.textContent = 'Você escolhe as partes exatas. Ex: "1-5" ou "3, 8-10".';
            }
        });
    }

    // ── Nome de arquivo nos inputs customizados ───────────────
    function setupFileInput(inputId, displayId) {
        const input = document.getElementById(inputId);
        const display = document.getElementById(displayId);
        if (!input || !display) return;
        input.addEventListener('change', function () {
            if (this.files?.length > 0) {
                display.textContent = this.files[0].name;
                display.style.color = 'var(--text)';
            } else {
                display.textContent = 'Nenhum arquivo selecionado';
                display.style.color = 'var(--muted)';
            }
        });
    }

    setupFileInput('splitInput',      'splitFileName');
    setupFileInput('protectInput',    'protectFileName');
    setupFileInput('unprotectInput',  'unprotectFileName');
    setupFileInput('compressInput',   'compressFileName');
    setupFileInput('watermarkInput',  'watermarkFileName');
    setupFileInput('extractInput',    'extractFileName');
    setupFileInput('manipulateInput', 'manipulateFileName');
    setupFileInput('mp4Input',        'mp4FileName');
    setupFileInput('mp4GifInput',     'mp4GifFileName');
    setupFileInput('qrLerInput',      'qrLerFileName');
    setupFileInput('paletaInput',     'paletaFileName');

    // ── Mesclar Planilhas: acumular arquivos ──────────────────
    const dtData = new DataTransfer();
    const mergeDataInput = document.getElementById('mergeDataInput');
    const mergeDataListContainer = document.getElementById('mergeDataListContainer');
    const mergeDataEmptyMsg = document.getElementById('mergeDataEmptyMsg');

    mergeDataInput?.addEventListener('change', function () {
        for (const file of this.files) { dtData.items.add(file); }
        this.files = dtData.files;
        mergeDataListContainer?.querySelectorAll('.merge-item').forEach(o => o.remove());
        if (dtData.files.length > 0 && mergeDataEmptyMsg) mergeDataEmptyMsg.style.display = 'none';
        for (const file of dtData.files) {
            const div = document.createElement('div');
            div.className = 'merge-item';
            div.textContent = 'D ' + file.name;
            div.style.cssText = 'font-size:12px;color:var(--text);background:var(--surface);padding:4px 8px;border-radius:4px;';
            mergeDataListContainer?.appendChild(div);
        }
    });

    // ── Leitor de QR Code (AJAX) ──────────────────────────────
    const qrLerForm = document.getElementById('qrLerForm');
    const qrLerResultado = document.getElementById('qrLerResultado');
    const qrLerBtn = document.getElementById('qrLerBtn');

    qrLerForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('qrLerInput');
        if (!fileInput?.files?.length) return;

        const formData = new FormData(qrLerForm);
        qrLerBtn.disabled = true;
        qrLerBtn.querySelector('span:first-child').textContent = 'Lendo...';

        try {
            const resp = await fetch('/api/qr/ler', { method: 'POST', body: formData });
            const data = await resp.json();

            if (data.erro) {
                qrLerResultado.innerHTML = `<span style="color:var(--accent2)">${data.erro}</span>`;
            } else {
                let html = '';
                for (const c of data.codigos) {
                    html += `<div style="margin-bottom:6px"><span style="color:var(--accent);font-weight:700">[${c.tipo}]</span> <span style="color:var(--text);cursor:pointer" title="Clique para copiar" onclick="navigator.clipboard.writeText('${c.dados.replace(/'/g, "\\'")}')"> ${c.dados}</span></div>`;
                }
                qrLerResultado.innerHTML = html;
            }
            qrLerResultado.style.display = 'block';
        } catch (err) {
            qrLerResultado.innerHTML = '<span style="color:var(--accent2)">Erro de conexão.</span>';
            qrLerResultado.style.display = 'block';
        } finally {
            qrLerBtn.disabled = false;
            qrLerBtn.querySelector('span:first-child').textContent = 'Ler QR Code';
        }
    });

    // ── Extrator de Paleta de Cores (AJAX) ────────────────────
    const paletaForm = document.getElementById('paletaForm');
    const paletaResultado = document.getElementById('paletaResultado');
    const paletaBtn = document.getElementById('paletaBtn');

    paletaForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('paletaInput');
        if (!fileInput?.files?.length) return;

        const formData = new FormData(paletaForm);
        paletaBtn.disabled = true;
        paletaBtn.querySelector('span:first-child').textContent = 'Extraindo...';

        try {
            const resp = await fetch('/api/img/paleta', { method: 'POST', body: formData });
            const data = await resp.json();

            if (data.erro) {
                paletaResultado.innerHTML = `<span style="color:var(--accent2)">${data.erro}</span>`;
            } else {
                let html = '<div class="paleta-swatches">';
                for (const c of data.paleta) {
                    html += `<div class="paleta-swatch" style="background:${c.hex}" title="${c.hex} — ${c.percentual}%" onclick="navigator.clipboard.writeText('${c.hex}')"><span class="paleta-swatch-label">${c.hex}</span></div>`;
                }
                html += '</div>';
                paletaResultado.innerHTML = html;
            }
            paletaResultado.style.display = 'block';
        } catch (err) {
            paletaResultado.innerHTML = '<span style="color:var(--accent2)">Erro de conexão.</span>';
            paletaResultado.style.display = 'block';
        } finally {
            paletaBtn.disabled = false;
            paletaBtn.querySelector('span:first-child').textContent = 'Extrair Cores';
        }
    });

    // ── Tempestade de ícones animados ─────────────────────────
    const stormContainer = document.getElementById('stormContainer');
    if (stormContainer) {
        const icones = [
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>',
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="3"></circle><circle cx="6" cy="18" r="3"></circle><line x1="20" y1="4" x2="8.12" y2="15.88"></line><line x1="14.47" y1="14.48" x2="20" y2="20"></line><line x1="8.12" y1="8.12" x2="12" y2="12"></line></svg>',
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>',
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'
        ];

        function spawnIcon() {
            const el = document.createElement('div');
            el.className = 'storm-icon';
            el.innerHTML = icones[Math.floor(Math.random() * icones.length)];
            const size = 14 + Math.random() * 14;
            el.style.width = el.style.height = size + 'px';
            el.style.opacity = (0.2 + Math.random() * 0.4).toString();
            el.style.top = (Math.random() * 12) + 'px';
            const duration = 6 + Math.random() * 8;
            el.style.animationDuration = duration + 's';
            stormContainer.appendChild(el);
            setTimeout(() => el.remove(), duration * 1000);
        }

        for (let i = 0; i < 40; i++) setTimeout(spawnIcon, i * 200);
        setInterval(spawnIcon, 400);
    }

    // ── Downloader de Mídia por Link com Barra de Progresso ────
    const formDownloadUrl = document.getElementById('formDownloadUrl');
    const inputUrlMedia = document.getElementById('inputUrlMedia');
    const btnIniciarDownloadUrl = document.getElementById('btnIniciarDownloadUrl');
    const progressContainerUrl = document.getElementById('progressContainerUrl');
    const progressStatusUrl = document.getElementById('progressStatusUrl');
    const progressPercentUrl = document.getElementById('progressPercentUrl');
    const progressFillUrl = document.getElementById('progressFillUrl');

    formDownloadUrl?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const urlVal = inputUrlMedia?.value?.trim();
        if (!urlVal) return;

        btnIniciarDownloadUrl.disabled = true;
        const btnTextSpan = btnIniciarDownloadUrl.querySelector('span:first-child');
        if (btnTextSpan) btnTextSpan.textContent = 'Processando...';

        if (progressContainerUrl) progressContainerUrl.style.display = 'flex';
        if (progressFillUrl) {
            progressFillUrl.style.width = '0%';
            progressFillUrl.style.background = '';
            progressFillUrl.style.boxShadow = '';
        }
        if (progressPercentUrl) {
            progressPercentUrl.style.display = 'inline';
            progressPercentUrl.textContent = '0%';
        }
        if (progressStatusUrl) {
            progressStatusUrl.textContent = 'Iniciando download...';
            progressStatusUrl.style.color = 'var(--accent)';
        }

        try {
            const formData = new FormData(formDownloadUrl);
            const resp = await fetch('/api/media/iniciar-download-url', {
                method: 'POST',
                body: formData
            });

            const data = await resp.json();

            if (!resp.ok || data.erro) {
                alert(data.erro || 'Não foi possível iniciar o download.');
                if (progressContainerUrl) progressContainerUrl.style.display = 'none';
                btnIniciarDownloadUrl.disabled = false;
                if (btnTextSpan) btnTextSpan.textContent = 'Baixar Mídia';
                return;
            }

            const jobId = data.job_id;

            // Loop de Polling para Progresso em Tempo Real
            const pollInterval = setInterval(async () => {
                try {
                    const statusResp = await fetch(`/api/media/download-status/${jobId}`);
                    const statusData = await statusResp.json();

                    if (statusData.erro) {
                        clearInterval(pollInterval);
                        if (progressStatusUrl) {
                            progressStatusUrl.textContent = statusData.erro;
                            progressStatusUrl.style.color = '#f87171';
                        }
                        if (progressPercentUrl) progressPercentUrl.style.display = 'none';
                        if (progressFillUrl) {
                            progressFillUrl.style.background = '#f87171';
                            progressFillUrl.style.boxShadow = '0 0 10px #f87171';
                        }
                        btnIniciarDownloadUrl.disabled = false;
                        if (btnTextSpan) btnTextSpan.textContent = 'Baixar Mídia';
                        return;
                    }

                    const pct = Math.min(100, Math.max(0, statusData.percent || 0));
                    if (progressFillUrl) progressFillUrl.style.width = `${pct}%`;
                    if (progressPercentUrl) progressPercentUrl.textContent = `${pct}%`;
                    if (progressStatusUrl && statusData.status) {
                        progressStatusUrl.textContent = statusData.status;
                    }

                    if (statusData.concluido && statusData.download_url) {
                        clearInterval(pollInterval);
                        if (progressFillUrl) progressFillUrl.style.width = '100%';
                        if (progressPercentUrl) progressPercentUrl.textContent = '100%';
                        if (progressStatusUrl) progressStatusUrl.textContent = 'Concluído! Baixando arquivo...';

                        // Iniciar o download automático do arquivo gerado
                        window.location.href = statusData.download_url;

                        setTimeout(() => {
                            btnIniciarDownloadUrl.disabled = false;
                            if (btnTextSpan) btnTextSpan.textContent = 'Baixar Mídia';
                        }, 3000);
                    }
                } catch (err) {
                    console.error('Erro ao consultar progresso:', err);
                }
            }, 600);

        } catch (err) {
            alert('Erro de conexão com o servidor.');
            if (progressContainerUrl) progressContainerUrl.style.display = 'none';
            btnIniciarDownloadUrl.disabled = false;
            if (btnTextSpan) btnTextSpan.textContent = 'Baixar Mídia';
        }
    });

}); // fim DOMContentLoaded
