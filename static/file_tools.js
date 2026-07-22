/**
 * file_tools.js — Script externo para a página Modificar Arquivos
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

    // ── File name display para inputs simples ─────────────────
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

    setupFileInput('criptoInput', 'criptoFileName');
    setupFileInput('decriptoInput', 'decriptoFileName');
    setupFileInput('hashInput', 'hashFileName');

    // ── Multi-file accumulators ───────────────────────────────
    function setupMultiFileAccumulator(inputId, containerId, emptyMsgId, prefix) {
        const dt = new DataTransfer();
        const input = document.getElementById(inputId);
        const container = document.getElementById(containerId);
        const emptyMsg = document.getElementById(emptyMsgId);

        if (!input || !container) return;

        input.addEventListener('change', function () {
            for (const file of this.files) { dt.items.add(file); }
            this.files = dt.files;
            container.querySelectorAll('.merge-item').forEach(o => o.remove());
            if (dt.files.length > 0 && emptyMsg) emptyMsg.style.display = 'none';
            for (const file of dt.files) {
                const div = document.createElement('div');
                div.className = 'merge-item';
                div.textContent = (prefix || '•') + ' ' + file.name;
                div.style.cssText = 'font-size:12px;color:var(--text);background:var(--surface);padding:4px 8px;border-radius:4px;';
                container.appendChild(div);
            }
        });
    }

    setupMultiFileAccumulator('comprimirInput', 'comprimirListContainer', 'comprimirEmptyMsg', '•');
    setupMultiFileAccumulator('zipSenhaInput', 'zipSenhaListContainer', 'zipSenhaEmptyMsg', '•');
    setupMultiFileAccumulator('renomearInput', 'renomearListContainer', 'renomearEmptyMsg', '•');

    // ── Calculadora de Hash (AJAX) ────────────────────────────
    const hashForm = document.getElementById('hashForm');
    const hashResultado = document.getElementById('hashResultado');
    const hashBtn = document.getElementById('hashBtn');

    hashForm?.addEventListener('submit', async (e) => {
        e.preventDefault();

        const fileInput = document.getElementById('hashInput');
        if (!fileInput?.files?.length) return;

        const formData = new FormData(hashForm);
        hashBtn.disabled = true;
        hashBtn.querySelector('span:first-child').textContent = 'Calculando...';

        try {
            const resp = await fetch('/api/file/hash', {
                method: 'POST',
                body: formData,
            });
            const data = await resp.json();

            if (data.erro) {
                hashResultado.innerHTML = `<span style="color:var(--accent2)">${data.erro}</span>`;
            } else {
                hashResultado.innerHTML = `
                    <div style="margin-bottom:8px;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:1px">${data.nome} — ${data.tamanho_formatado}</div>
                    <div><span class="hash-label">MD5: </span><span class="hash-value" title="Clique para copiar" data-hash="${data.md5}">${data.md5}</span></div>
                    <div><span class="hash-label">SHA-1: </span><span class="hash-value" title="Clique para copiar" data-hash="${data.sha1}">${data.sha1}</span></div>
                    <div><span class="hash-label">SHA-256: </span><span class="hash-value" title="Clique para copiar" data-hash="${data.sha256}">${data.sha256}</span></div>
                `;

                // Click to copy
                hashResultado.querySelectorAll('.hash-value').forEach(el => {
                    el.addEventListener('click', () => {
                        navigator.clipboard.writeText(el.dataset.hash).then(() => {
                            const original = el.textContent;
                            el.textContent = '✓ copiado!';
                            el.style.color = 'var(--accent)';
                            setTimeout(() => {
                                el.textContent = original;
                                el.style.color = '';
                            }, 1500);
                        });
                    });
                });
            }

            hashResultado.style.display = 'block';
        } catch (err) {
            hashResultado.innerHTML = '<span style="color:var(--accent2)">Erro de conexão.</span>';
            hashResultado.style.display = 'block';
        } finally {
            hashBtn.disabled = false;
            hashBtn.querySelector('span:first-child').textContent = 'Calcular Hash';
        }
    });

    // ── Kinetic Vector Rail Top Bar ───────────────────────────
    const stormContainer = document.getElementById('stormContainer');
    if (stormContainer) {
        stormContainer.innerHTML = `
            <div class="kinetic-rail-line"></div>
            <div class="kinetic-pulse-beam"></div>
            <div class="kinetic-pulse-beam-rev"></div>
            <div class="kinetic-nodes-track" id="kineticNodesTrack"></div>
        `;

        const track = document.getElementById('kineticNodesTrack');
        const nodesData = [
            { type: 'node-encrypt', svg: '<svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>' },
            { type: 'node-compress', svg: '<svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>' },
            { type: 'node-hash', svg: '<svg viewBox="0 0 24 24"><line x1="4" y1="9" x2="20" y2="9"></line><line x1="4" y1="15" x2="20" y2="15"></line><line x1="10" y1="3" x2="8" y2="21"></line><line x1="16" y1="3" x2="14" y2="21"></line></svg>' },
            { type: 'node-encrypt', svg: '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>' },
            { type: 'node-compress', svg: '<svg viewBox="0 0 24 24"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>' },
            { type: 'node-hash', svg: '<svg viewBox="0 0 24 24"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>' },
            { type: 'node-encrypt', svg: '<svg viewBox="0 0 24 24"><path d="M21 2l-2 2m-3 3l-6.5 6.5a4.5 4.5 0 1 1-2-2L14 5l3-3 4 4z"></path></svg>' },
            { type: 'node-compress', svg: '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>' },
            { type: 'node-hash', svg: '<svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line></svg>' },
            { type: 'node-compress', svg: '<svg viewBox="0 0 24 24"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>' },
            { type: 'node-encrypt', svg: '<svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"></rect><path d="M7 11V7a5 5 0 0 1 9.9-1"></path></svg>' },
            { type: 'node-hash', svg: '<svg viewBox="0 0 24 24"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>' },
            { type: 'node-compress', svg: '<svg viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>' },
            { type: 'node-hash', svg: '<svg viewBox="0 0 24 24"><path d="M8 3H5a2 2 0 0 0-2 2v3m0 8v3a2 2 0 0 0 2 2h3m8-18h3a2 2 0 0 1 2 2v3m0 8v3a2 2 0 0 1-2 2h-3"></path></svg>' }
        ];

        nodesData.forEach((data, idx) => {
            const el = document.createElement('div');
            el.className = `kinetic-vector-node ${data.type}`;
            el.innerHTML = data.svg;
            el.style.animationDelay = `${(idx * 0.45).toFixed(2)}s`;
            track?.appendChild(el);
        });
    }

}); // fim DOMContentLoaded
