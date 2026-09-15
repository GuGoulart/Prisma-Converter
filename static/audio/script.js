/**
 * script.js — Prisma Audio
 * Lógica do frontend para as 6 ferramentas de áudio.
 */

'use strict';

// ── Helper CSRF ────────────────────────────────────────────────
function getCsrf() {
    return document.querySelector('meta[name="csrf-token"]')?.content || '';
}

function csrfFetch(url, options = {}) {
    const headers = Object.assign({ 'X-CSRFToken': getCsrf() }, options.headers || {});
    return fetch(url, Object.assign({}, options, { headers }));
}

// ── Heartbeat (desktop auto-shutdown) ─────────────────────────
setInterval(() => {
    fetch('/api/heartbeat', { method: 'POST' }).catch(() => {});
}, 3000);

// ── Estado da aplicação ───────────────────────────────────────
const _arquivos = {}; // { conv: File|null, cut: ..., etc }
const _joinFiles = []; // array de File para o joiner

// ── Toggle de cards ───────────────────────────────────────────
function toggleCard(id) {
    const card = document.getElementById(`ferramenta-${id}`);
    if (!card) return;
    const isAtivo = card.classList.contains('ativo');
    // Fecha todos
    document.querySelectorAll('.tool-card').forEach(c => c.classList.remove('ativo'));
    // Abre o clicado (se estava fechado)
    if (!isAtivo) {
        card.classList.add('ativo');
        // Scroll suave
        setTimeout(() => {
            card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    }
}

// Abre o primeiro card por padrão
document.addEventListener('DOMContentLoaded', () => {
    const primeiro = document.querySelector('.tool-card');
    if (primeiro) primeiro.classList.add('ativo');
    setupMobileMenu();
    setupDragDrop();
    setupSidebarLinks();
});

// ── Mobile Menu ───────────────────────────────────────────────
function setupMobileMenu() {
    const btn = document.getElementById('menuBtn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('drawerOverlay');

    if (!btn || !sidebar || !overlay) return;

    btn.addEventListener('click', () => {
        sidebar.classList.toggle('aberto');
        overlay.classList.toggle('ativo');
        overlay.style.display = sidebar.classList.contains('aberto') ? 'block' : 'none';
    });

    overlay.addEventListener('click', () => {
        sidebar.classList.remove('aberto');
        overlay.classList.remove('ativo');
        overlay.style.display = 'none';
    });
}

// ── Sidebar links scroll (fecha menu mobile e rola até a ferramenta) ──
function setupSidebarLinks() {
    document.querySelectorAll('.sidebar-tool-chip').forEach(link => {
        link.addEventListener('click', (e) => {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('drawerOverlay');
            if (sidebar && sidebar.classList.contains('aberto')) {
                sidebar.classList.remove('aberto');
                overlay.classList.remove('ativo');
                overlay.style.display = 'none';
            }
            const href = link.getAttribute('href');
            if (href && href.startsWith('#ferramenta-')) {
                e.preventDefault();
                const card = document.querySelector(href);
                if (card) {
                    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    card.style.borderColor = 'var(--accent)';
                    setTimeout(() => { card.style.borderColor = ''; }, 1500);
                }
            }
        });
    });
}

// ── Drag & Drop ───────────────────────────────────────────────
function setupDragDrop() {
    document.querySelectorAll('.upload-zone').forEach(zone => {
        zone.addEventListener('dragover', e => {
            e.preventDefault();
            zone.classList.add('drag-over');
        });
        zone.addEventListener('dragleave', () => {
            zone.classList.remove('drag-over');
        });
        zone.addEventListener('drop', e => {
            e.preventDefault();
            zone.classList.remove('drag-over');
            const files = e.dataTransfer?.files;
            if (!files || !files.length) return;

            // Descobre o ID da ferramenta pelo id do zone
            const zoneId = zone.id; // ex: "upload-conv"
            const toolId = zoneId.replace('upload-', '');

            if (toolId === 'join') {
                // Drop no joiner: adiciona todos os arquivos à lista
                for (const file of files) {
                    adicionarArquivoJoinItem(file);
                }
            } else {
                // Simula seleção de arquivo no input
                const input = zone.querySelector('input[type="file"]');
                if (input) {
                    const dt = new DataTransfer();
                    dt.items.add(files[0]);
                    input.files = dt.files;
                    arquivoSelecionado(toolId, input);
                }
            }
        });
    });

    // Drag & drop na zona do joiner
    const joinZone = document.querySelector('.upload-multi-zone');
    if (joinZone) {
        joinZone.addEventListener('dragover', e => {
            e.preventDefault();
            joinZone.style.borderColor = 'var(--accent)';
        });
        joinZone.addEventListener('dragleave', () => {
            joinZone.style.borderColor = '';
        });
        joinZone.addEventListener('drop', e => {
            e.preventDefault();
            joinZone.style.borderColor = '';
            const files = e.dataTransfer?.files;
            if (!files) return;
            for (const file of files) {
                adicionarArquivoJoinItem(file);
            }
        });
    }
}

// ── Trigger de upload ─────────────────────────────────────────
function triggerUpload(id) {
    const input = document.getElementById(`arquivo-${id}`);
    if (input) input.click();
}

// ── Arquivo selecionado ───────────────────────────────────────
function arquivoSelecionado(id, input) {
    if (!input.files || !input.files.length) return;
    const file = input.files[0];
    _arquivos[id] = file;

    const zone = document.getElementById(`upload-${id}`);
    const titulo = document.getElementById(`titulo-${id}`);
    const nomeEl = document.getElementById(`nome-${id}`);
    const statusEl = document.getElementById(`status-${id}`);

    const fileInfo = `${file.name} (${formatarTamanho(file.size)})`;

    if (zone) zone.classList.add('tem-arquivo');
    if (titulo) titulo.textContent = 'Arquivo selecionado';
    if (nomeEl) {
        nomeEl.textContent = fileInfo;
        nomeEl.style.display = 'block';
    }
    if (statusEl) {
        statusEl.textContent = fileInfo;
        statusEl.classList.add('tem-arquivo');
    }

    // Limpa resultados anteriores
    resetResultado(id);

    // Para o cutter: busca a duração e inicializa o preview interativo
    if (id === 'cut') {
        buscarDuracao(file);
        carregarPreviewCortador(file);
    }
}

// ── Cortador de Áudio: Sliders e Preview Player Interativos ─────
let _audioPreviewUrl = null;

function formatarSegundosEmTempo(seg) {
    if (isNaN(seg) || seg < 0) return '0:00';
    const mins = Math.floor(seg / 60);
    const secs = Math.floor(seg % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function tempoParaSegundos(str) {
    if (!str) return 0;
    const partes = str.toString().trim().split(':');
    if (partes.length === 2) {
        return (parseInt(partes[0], 10) || 0) * 60 + (parseFloat(partes[1]) || 0);
    }
    return parseFloat(str) || 0;
}

function carregarPreviewCortador(file) {
    const wrap = document.getElementById('cut-interactive-wrap');
    const audio = document.getElementById('audio-preview-cut');
    const sliderInicio = document.getElementById('slider-inicio-cut');
    const sliderFim = document.getElementById('slider-fim-cut');
    const badgeInicio = document.getElementById('badge-inicio-cut');
    const badgeFim = document.getElementById('badge-fim-cut');
    const inputInicio = document.getElementById('inicio-cut');
    const inputFim = document.getElementById('fim-cut');
    const previewTotal = document.getElementById('preview-total-cut');
    const previewCurr = document.getElementById('preview-curr-cut');

    if (!wrap || !audio) return;

    if (_audioPreviewUrl) {
        URL.revokeObjectURL(_audioPreviewUrl);
        _audioPreviewUrl = null;
    }

    _audioPreviewUrl = URL.createObjectURL(file);
    audio.src = _audioPreviewUrl;

    audio.onloadedmetadata = () => {
        const dur = audio.duration;
        if (!dur || isNaN(dur)) return;

        sliderInicio.disabled = false;
        sliderFim.disabled = false;

        sliderInicio.min = '0';
        sliderInicio.max = dur.toString();
        sliderInicio.value = '0';

        sliderFim.min = '0';
        sliderFim.max = dur.toString();
        sliderFim.value = dur.toString();

        const durFmt = formatarSegundosEmTempo(dur);
        if (previewTotal) previewTotal.textContent = durFmt;
        if (badgeInicio) badgeInicio.textContent = '0:00';
        if (badgeFim) badgeFim.textContent = durFmt;

        if (inputInicio) inputInicio.value = '0:00';
        if (inputFim) inputFim.value = durFmt;

        wrap.style.display = 'flex';
    };

    audio.ontimeupdate = () => {
        if (!audio.duration) return;
        if (previewCurr) previewCurr.textContent = formatarSegundosEmTempo(audio.currentTime);

        const endSec = parseFloat(sliderFim.value) || audio.duration;
        if (audio.currentTime >= endSec) {
            audio.pause();
            audio.currentTime = parseFloat(sliderInicio.value) || 0;
            atualizarIconePreview(false);
        }
    };
}

function onCutSliderInput(tipo) {
    const audio = document.getElementById('audio-preview-cut');
    const sliderInicio = document.getElementById('slider-inicio-cut');
    const sliderFim = document.getElementById('slider-fim-cut');
    const badgeInicio = document.getElementById('badge-inicio-cut');
    const badgeFim = document.getElementById('badge-fim-cut');
    const inputInicio = document.getElementById('inicio-cut');
    const inputFim = document.getElementById('fim-cut');

    let valInicio = isNaN(parseFloat(sliderInicio.value)) ? 0 : parseFloat(sliderInicio.value);
    let valFim = isNaN(parseFloat(sliderFim.value)) ? (audio?.duration || 100) : parseFloat(sliderFim.value);

    if (tipo === 'inicio') {
        if (valInicio >= valFim) {
            valInicio = Math.max(0, valFim - 0.5);
            sliderInicio.value = valInicio;
        }
        const fmt = formatarSegundosEmTempo(valInicio);
        if (badgeInicio) badgeInicio.textContent = fmt;
        if (inputInicio) inputInicio.value = fmt;
        if (audio && !audio.paused) {
            audio.currentTime = valInicio;
        }
    } else if (tipo === 'fim') {
        if (valFim <= valInicio) {
            valFim = Math.min(sliderFim.max, valInicio + 0.5);
            sliderFim.value = valFim;
        }
        const fmt = formatarSegundosEmTempo(valFim);
        if (badgeFim) badgeFim.textContent = fmt;
        if (inputFim) inputFim.value = fmt;
    }
}

function onCutInputChange(tipo) {
    const sliderInicio = document.getElementById('slider-inicio-cut');
    const sliderFim = document.getElementById('slider-fim-cut');
    const inputInicio = document.getElementById('inicio-cut');
    const inputFim = document.getElementById('fim-cut');
    const badgeInicio = document.getElementById('badge-inicio-cut');
    const badgeFim = document.getElementById('badge-fim-cut');

    if (tipo === 'inicio' && inputInicio && sliderInicio) {
        const sec = tempoParaSegundos(inputInicio.value);
        if (!isNaN(sec) && sec >= 0 && sec <= parseFloat(sliderInicio.max)) {
            sliderInicio.value = sec;
            if (badgeInicio) badgeInicio.textContent = formatarSegundosEmTempo(sec);
        }
    } else if (tipo === 'fim' && inputFim && sliderFim) {
        const sec = tempoParaSegundos(inputFim.value);
        if (!isNaN(sec) && sec >= 0 && sec <= parseFloat(sliderFim.max)) {
            sliderFim.value = sec;
            if (badgeFim) badgeFim.textContent = formatarSegundosEmTempo(sec);
        }
    }
}

function togglePreviewCortador() {
    const audio = document.getElementById('audio-preview-cut');
    const sliderInicio = document.getElementById('slider-inicio-cut');
    const sliderFim = document.getElementById('slider-fim-cut');
    if (!audio || !audio.src) {
        triggerUpload('cut');
        return;
    }

    if (audio.paused) {
        const startSec = parseFloat(sliderInicio.value) || 0;
        const endSec = parseFloat(sliderFim.value) || audio.duration;
        if (audio.currentTime < startSec || audio.currentTime >= endSec) {
            audio.currentTime = startSec;
        }
        audio.play().then(() => {
            atualizarIconePreview(true);
        }).catch(() => {});
    } else {
        audio.pause();
        atualizarIconePreview(false);
    }
}

function atualizarIconePreview(tocando) {
    const iconPlay = document.getElementById('icon-play-cut');
    const iconPause = document.getElementById('icon-pause-cut');
    const label = document.getElementById('label-play-preview-cut');

    if (tocando) {
        if (iconPlay) iconPlay.style.display = 'none';
        if (iconPause) iconPause.style.display = 'inline';
        if (label) label.textContent = 'Pausar Preview';
    } else {
        if (iconPlay) iconPlay.style.display = 'inline';
        if (iconPause) iconPause.style.display = 'none';
        if (label) label.textContent = 'Ouvir Trecho Selecionado';
    }
}

// ── Buscar duração (Audio Cutter) ─────────────────────────────
async function buscarDuracao(file) {
    const wrap = document.getElementById('duracao-cut-wrap');
    const val = document.getElementById('duracao-cut-valor');
    if (!wrap || !val) return;

    wrap.style.display = 'none';
    val.textContent = '...';

    try {
        const fd = new FormData();
        fd.append('arquivo', file);
        fd.append('csrf_token', getCsrf());

        const res = await csrfFetch('/api/duracao', { method: 'POST', body: fd });
        const data = await res.json();

        if (data.ok) {
            val.textContent = data.duracao_fmt;
            wrap.style.display = 'block';
            // Preenche o campo "fim" com a duração total
            const fimInput = document.getElementById('fim-cut');
            if (fimInput && !fimInput.value) {
                fimInput.value = data.duracao_fmt;
            }
        }
    } catch (e) {
        // Silencioso — duração é opcional
    }
}

// ── Seleção de chip ───────────────────────────────────────────
function selecionarChip(inputId, valor, chipEl) {
    // Desmarca todos os chips do mesmo grupo
    const parent = chipEl.closest('.opcoes-chips');
    if (parent) {
        parent.querySelectorAll('.opcao-chip').forEach(c => c.classList.remove('selecionado'));
    }
    chipEl.classList.add('selecionado');

    const input = document.getElementById(inputId);
    if (input) input.value = valor;
}

function atualizarHudConv() {
    const bitrate = document.getElementById('bitrate-conv')?.value || '192k';
    const channels = document.getElementById('channels-conv')?.value || '2';
    const sample = document.getElementById('sample-conv')?.value || '44100';

    const chStr = channels === '1' ? 'Mono' : 'Estéreo';
    const smpStr = sample === '48000' ? '48.0 kHz' : '44.1 kHz';
    const display = document.getElementById('hud-sample-display');

    if (display) {
        display.textContent = `${smpStr} · ${chStr} (${bitrate})`;
    }
}

// ── Atualizar display de velocidade ───────────────────────────
function atualizarVelocidade(val) {
    const display = document.getElementById('valor-spd');
    if (display) display.textContent = parseFloat(val).toFixed(2) + '×';
}

// ── Audio Joiner: gerenciar lista de arquivos ─────────────────
function adicionarArquivosJoin(input) {
    if (!input.files) return;
    for (const file of input.files) {
        adicionarArquivoJoinItem(file);
    }
    // Limpa o input para permitir re-seleção do mesmo arquivo
    input.value = '';
}

function adicionarArquivoJoinItem(file) {
    // Verifica extensão básica
    const ext = file.name.split('.').pop().toLowerCase();
    const extsPermitidas = ['mp3','wav','aac','ogg','flac','m4a','opus','wma'];
    if (!extsPermitidas.includes(ext)) {
        mostrarToast(`Arquivo ignorado: ${file.name} (formato não suportado)`, true);
        return;
    }

    _joinFiles.push(file);
    renderizarListaJoin();
    resetResultado('join');
}

function removerArquivoJoin(index) {
    _joinFiles.splice(index, 1);
    renderizarListaJoin();
}

function renderizarListaJoin() {
    const lista = document.getElementById('files-list-join');
    const empty = document.getElementById('empty-join');
    if (!lista) return;

    // Limpa (exceto o empty)
    Array.from(lista.children).forEach(child => {
        if (child !== empty) child.remove();
    });

    if (_joinFiles.length === 0) {
        if (empty) empty.style.display = 'block';
        return;
    }

    if (empty) empty.style.display = 'none';

    _joinFiles.forEach((file, i) => {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <span class="file-item-num">${String(i + 1).padStart(2, '0')}</span>
            <span class="file-item-name" title="${file.name}">${file.name}</span>
            <span class="file-item-size">${formatarTamanho(file.size)}</span>
            <button class="file-item-remove" onclick="removerArquivoJoin(${i})" title="Remover">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        `;
        lista.appendChild(item);
    });
}

// ── Processar ferramentas (conv, cut, vol, spd, rev) ──────────
async function processarFerramenta(id) {
    const arquivo = _arquivos[id];
    if (!arquivo) {
        mostrarErro(id, 'Selecione um arquivo de áudio antes de continuar.');
        return;
    }

    const btn = document.getElementById(`btn-${id}`);
    resetResultado(id);
    iniciarProcessamento(id, btn);

    try {
        const fd = new FormData();
        fd.append('arquivo', arquivo);
        fd.append('csrf_token', getCsrf());

        // Adiciona parâmetros específicos de cada ferramenta
        switch (id) {
            case 'conv':
                fd.append('formato', document.getElementById('formato-conv')?.value || 'mp3');
                fd.append('bitrate', document.getElementById('bitrate-conv')?.value || '192k');
                break;
            case 'cut':
                fd.append('inicio', document.getElementById('inicio-cut')?.value || '0:00');
                fd.append('fim', document.getElementById('fim-cut')?.value || '');
                break;
            case 'vol':
                fd.append('ajuste', document.getElementById('ajuste-vol')?.value || '+6');
                break;
            case 'spd':
                fd.append('fator', document.getElementById('fator-spd')?.value || '1.5');
                break;
            case 'rev':
                // Sem parâmetros extras
                break;
        }

        // Mapeamento de ID → endpoint
        const endpoints = {
            conv: '/api/converter',
            cut:  '/api/cortar',
            vol:  '/api/volume',
            spd:  '/api/velocidade',
            rev:  '/api/inverter',
        };

        const url = endpoints[id];
        if (!url) throw new Error('Ferramenta desconhecida');

        const res = await csrfFetch(url, { method: 'POST', body: fd });
        const data = await res.json();

        if (!res.ok || data.erro) {
            throw new Error(data.erro || `Erro ${res.status}`);
        }

        mostrarResultado(id, data, btn);

    } catch (err) {
        finalizarProcessamento(id, btn);
        mostrarErro(id, err.message || 'Erro desconhecido. Tente novamente.');
    }
}

// ── Processar Joiner (múltiplos arquivos) ─────────────────────
async function processarJoiner() {
    if (_joinFiles.length < 2) {
        mostrarErro('join', 'Adicione pelo menos 2 arquivos para juntar.');
        return;
    }

    const btn = document.getElementById('btn-join');
    resetResultado('join');
    iniciarProcessamento('join', btn);

    try {
        const fd = new FormData();
        fd.append('csrf_token', getCsrf());
        _joinFiles.forEach(file => fd.append('arquivos', file));
        fd.append('formato', document.getElementById('formato-join')?.value || 'mp3');
        fd.append('bitrate', document.getElementById('bitrate-join')?.value || '192k');

        const res = await csrfFetch('/api/juntar', { method: 'POST', body: fd });
        const data = await res.json();

        if (!res.ok || data.erro) {
            throw new Error(data.erro || `Erro ${res.status}`);
        }

        mostrarResultado('join', data, btn);

    } catch (err) {
        finalizarProcessamento('join', btn);
        mostrarErro('join', err.message || 'Erro ao juntar os áudios.');
    }
}

// ── UI: sistema de progresso com porcentagem em tempo real ──────
const _progressTimers = {};
const _progressPct = {};

function iniciarProcessamento(id, btn) {
    if (_progressTimers[id]) {
        clearInterval(_progressTimers[id]);
        delete _progressTimers[id];
    }

    _progressPct[id] = 0;

    const progressWrap = document.getElementById(`progress-${id}`);
    const fill = document.getElementById(`fill-${id}`);
    const label = document.getElementById(`label-${id}`);
    const pctEl = document.getElementById(`pct-${id}`);

    if (progressWrap) progressWrap.classList.add('visivel');
    if (fill) fill.style.width = '0%';
    if (pctEl) pctEl.textContent = '0%';

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span>Processando...</span><div class="spinner"></div>`;
    }

    _progressTimers[id] = setInterval(() => {
        if (_progressPct[id] < 92) {
            let increment = 1;
            if (_progressPct[id] < 30) increment = Math.floor(Math.random() * 4) + 3;
            else if (_progressPct[id] < 70) increment = Math.floor(Math.random() * 3) + 2;
            else increment = 1;

            _progressPct[id] = Math.min(92, _progressPct[id] + increment);
            
            const currPct = _progressPct[id];
            if (fill) fill.style.width = `${currPct}%`;
            if (pctEl) pctEl.textContent = `${currPct}%`;
        }
    }, 110);
}

// ── UI: finalizar processamento (erro ou sucesso) ─────────────
function finalizarProcessamento(id, btn, textoOriginal = null) {
    if (_progressTimers[id]) {
        clearInterval(_progressTimers[id]);
        delete _progressTimers[id];
    }

    const fill = document.getElementById(`fill-${id}`);
    const pctEl = document.getElementById(`pct-${id}`);

    if (fill) fill.style.width = '100%';
    if (pctEl) pctEl.textContent = '100%';

    setTimeout(() => {
        if (btn) {
            btn.disabled = false;
            const labels = {
                conv: 'Converter Áudio',
                cut:  'Cortar Áudio',
                join: 'Juntar Áudios',
                vol:  'Ajustar Volume',
                spd:  'Alterar Velocidade',
                rev:  'Inverter Áudio',
                trns: 'Transcrever Áudio'
            };
            const arrows = {
                conv: '↓', cut: '✂', join: '+', vol: '↑', spd: '▶▶', rev: '↩', trns: '📝'
            };
            btn.innerHTML = `<span>${textoOriginal || labels[id] || 'Processar'}</span><span class="botao-arr">${arrows[id] || '↓'}</span>`;
        }

        const progressWrap = document.getElementById(`progress-${id}`);
        if (progressWrap) progressWrap.classList.remove('visivel');
        if (fill) fill.style.width = '0%';
        if (pctEl) pctEl.textContent = '0%';
    }, 450);
}

// ── UI: mostrar resultado de sucesso ──────────────────────────
function mostrarResultado(id, data, btn) {
    finalizarProcessamento(id, btn);

    // Dispara o download diretamente no navegador sem precisar de botão manual
    if (data.url_download) {
        const link = document.createElement('a');
        link.href = data.url_download;
        link.setAttribute('download', data.nome_download || 'audio_prisma');
        document.body.appendChild(link);
        link.click();
        link.remove();
    }

    mostrarToast('Pronto! Áudio baixado automaticamente.');
}

// ── UI: mostrar erro ──────────────────────────────────────────
function mostrarErro(id, mensagem) {
    const erroWrap = document.getElementById(`erro-${id}`);
    const erroMsg = document.getElementById(`erro-msg-${id}`);

    if (erroWrap) erroWrap.classList.add('visivel', 'erro');
    if (erroMsg) erroMsg.textContent = mensagem;

    mostrarToast(mensagem, true);
}

// ── UI: reset estado de resultado ─────────────────────────────
function resetResultado(id) {
    const resultadoWrap = document.getElementById(`resultado-${id}`);
    const erroWrap = document.getElementById(`erro-${id}`);

    if (resultadoWrap) resultadoWrap.classList.remove('visivel');
    if (erroWrap) erroWrap.classList.remove('visivel', 'erro');
}

// ── Toast notification ────────────────────────────────────────
let _toastTimer = null;

function mostrarToast(msg, isErro = false) {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toastMsg');
    const toastIcone = toast?.querySelector('.toast-icone');

    if (!toast || !toastMsg) return;

    toastMsg.textContent = msg;
    if (toastIcone) toastIcone.textContent = isErro ? '✕' : '✓';
    toast.classList.toggle('erro', isErro);
    toast.classList.add('visivel');

    if (_toastTimer) clearTimeout(_toastTimer);
    _toastTimer = setTimeout(() => toast.classList.remove('visivel'), 4000);
}

// ── Utilitário: formatar tamanho ──────────────────────────────
function formatarTamanho(bytes) {
    if (!bytes) return '0 B';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
}

// ── FERRAMENTA: Transcritor de Áudio (Speech-to-Text) ─────────
async function processarTranscritor() {
    const btn = document.getElementById('btn-trns');
    const inputArquivo = document.getElementById('arquivo-trns');
    const inputIdioma = document.getElementById('idioma-trns');
    const inputModelo = document.getElementById('modelo-trns');
    const previewWrap = document.getElementById('wrap-preview-trns');
    const textareaResultado = document.getElementById('texto-resultado-trns');

    if (!inputArquivo || !inputArquivo.files || inputArquivo.files.length === 0) {
        mostrarErro('trns', 'Por favor, selecione um arquivo de áudio para transcrever.');
        return;
    }

    iniciarProcessamento('trns', btn);
    if (previewWrap) previewWrap.style.display = 'flex';

    const formData = new FormData();
    formData.append('arquivo', inputArquivo.files[0]);
    formData.append('idioma', inputIdioma ? inputIdioma.value : 'auto');
    formData.append('formato', inputFormato ? inputFormato.value : 'txt');
    formData.append('modelo', inputModelo ? inputModelo.value : 'small');
    formData.append('csrf_token', getCsrf());

    try {
        const response = await csrfFetch('/api/transcrever', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok || !data.ok) {
            mostrarErro('trns', data.erro || 'Erro ao transcrever o áudio.');
            finalizarProcessamento('trns', btn);
            return;
        }

        // Exibe o texto transcrito na tela e preserva no editor
        if (textareaResultado) {
            textareaResultado.value = data.texto || '';
            atualizarContadorTextoTrns();
        }

        finalizarProcessamento('trns', btn);
        mostrarToast('Transcrição concluída com sucesso!');

        // Baixa o arquivo sem recarregar a página ou perder o texto
        baixarTextoTranscricao();

    } catch (err) {
        console.error('[transcrever] Erro:', err);
        mostrarErro('trns', 'Erro de conexão com o servidor. Tente novamente.');
        finalizarProcessamento('trns', btn);
    }
}

function copiarTranscricao() {
    const textareaResultado = document.getElementById('texto-resultado-trns');
    if (!textareaResultado || !textareaResultado.value) return;

    navigator.clipboard.writeText(textareaResultado.value).then(() => {
        mostrarToast('Texto copiado para a área de transferência!');
    }).catch(() => {
        textareaResultado.select();
        document.execCommand('copy');
        mostrarToast('Texto copiado para a área de transferência!');
    });
}

function baixarTextoTranscricao() {
    const textareaResultado = document.getElementById('texto-resultado-trns');
    const inputFormato = document.getElementById('formato-trns');
    if (!textareaResultado || !textareaResultado.value) {
        mostrarToast('Não há texto para baixar.', true);
        return;
    }

    const fmt = inputFormato ? inputFormato.value : 'txt';
    const conteudo = textareaResultado.value;
    const blob = new Blob([conteudo], { type: 'text/plain;charset=utf-8' 

    // ════════════════════════════════════════════════════════════════════════════
    // ── GESTÃO DO HISTÓRICO DE ARQUIVOS E AUTODESTRUIÇÃO ─────────────────────────
    // ════════════════════════════════════════════════════════════════════════════

    function iniciarCronometrosHistorico() {
        const histItems = document.querySelectorAll(".historico-item");
        if (!histItems.length) return;

        function atualizarTimers() {
            const agora = Math.floor(Date.now() / 1000);
            const lang = typeof getCurrentLang === "function" ? getCurrentLang() : "pt";
            const dict = typeof translations !== "undefined" ? translations[lang] || {} : {};
            const deletedLabel = dict["conv.history.deleted"] || "Conteúdo Apagado";

            histItems.forEach((item) => {
                const isApagado = item.getAttribute("data-apagado") === "true";
                const expiraStr = item.getAttribute("data-expires");
                if (isApagado) return;

                if (expiraStr) {
                    const expiraEm = parseInt(expiraStr, 10);
                    const restante = expiraEm - agora;

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
                        atualizarEstadoDownloadLote();
                    } else if (timerValSpan) {
                        const m = Math.floor(restante / 60);
                        const s = restante % 60;
                        timerValSpan.textContent = `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
                    }
                }
            });
        }

        atualizarTimers();
        setInterval(atualizarTimers, 1000);
    }

    iniciarCronometrosHistorico();

    window.restaurarArquivo = async function (jobId) {
        if (!jobId) return;
        try {
            const resp = await csrfFetch("/api/historico/restaurar/" + jobId, {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            const data = await resp.json();
            const lang = typeof getCurrentLang === "function" ? getCurrentLang() : "pt";
            const dict = typeof translations !== "undefined" ? translations[lang] || {} : {};

            if (!resp.ok || data.erro) {
                mostrarToast(data.erro || "Não foi possível restaurar o arquivo.");
                return;
            }

            const items = document.querySelectorAll(`.historico-item[data-job-id="${jobId}"]`);
            items.forEach((el) => {
                el.setAttribute("data-expires", data.expira_em);
                el.setAttribute("data-apagado", "false");
            });

            const msg = dict["conv.history.restoreToast"] || data.mensagem || "Arquivo restaurado com sucesso!";
            mostrarToast(msg);
            window.setTimeout(() => window.location.reload(), 400);
        } catch (err) {
            mostrarToast(err.message || "Erro ao conectar com o servidor.");
        }
    };

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
            mostrarToast("Gerando arquivo ZIP...");
            const response = await fetch("/api/historico/zip-todos");
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.erro || "Não há arquivos disponíveis para download.");
            }
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = "prisma_audio_lote.zip";
            link.click();
            URL.revokeObjectURL(url);
            mostrarToast("ZIP baixado com sucesso.");
        } catch (error) {
            mostrarToast(error.message || "Não foi possível gerar o ZIP.");
        }
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
    destroyModal?.addEventListener("click", (event) => {
        if (event.target === destroyModal) fecharModalDestruir();
    });

    document.getElementById("confirmDestroyHistory")?.addEventListener("click", async () => {
        try {
            const response = await csrfFetch("/api/historico/destruir-tudo", { method: "POST" });
            const data = await response.json();
            if (!response.ok || data.erro) throw new Error(data.erro || "Falha ao destruir os arquivos.");
            fecharModalDestruir();

            const histItems = document.querySelectorAll(".historico-item");
            histItems.forEach((item) => item.setAttribute("data-apagado", "true"));
            atualizarEstadoDownloadLote();

            mostrarToast(data.mensagem || "Arquivos destruídos.");
            window.setTimeout(() => window.location.reload(), 500);
        } catch (error) {
            mostrarToast(error.message || "Não foi possível destruir os arquivos.");
        }
    });

    const retentionRoot = document.getElementById("historyRetention");
    function atualizarRetencaoSelecionada(policy) {
        retentionRoot?.querySelectorAll(".btn-ret-opt").forEach((button) => {
            button.classList.toggle("active", button.dataset.policy === policy);
        });
    }
    atualizarRetencaoSelecionada(document.body.dataset.retentionPolicy || "15min");
    retentionRoot?.addEventListener("click", async (event) => {
        const button = event.target.closest(".btn-ret-opt");
        if (!button) return;
        const politica = button.dataset.policy;
        try {
            const response = await csrfFetch("/api/historico/set-politica", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ politica })
            });
            const data = await response.json();
            if (!response.ok || data.erro) throw new Error(data.erro || "Falha ao salvar preferência.");
            document.body.dataset.retentionPolicy = politica;
            atualizarRetencaoSelecionada(politica);
            mostrarToast("Preferência de retenção atualizada.");
        } catch (error) {
            mostrarToast(error.message || "Não foi possível salvar a preferência.");
        }
    });

});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcricao_prisma.${fmt}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    mostrarToast('Arquivo de transcrição baixado com sucesso!');
}

async function colarTextoTranscricao() {
    const textareaResultado = document.getElementById('texto-resultado-trns');
    if (!textareaResultado) return;

    try {
        const text = await navigator.clipboard.readText();
        if (text) {
            textareaResultado.value = text;
            atualizarContadorTextoTrns();
            mostrarToast('Texto colado com sucesso!');
        }
    } catch (e) {
        textareaResultado.focus();
        mostrarToast('Pressione Ctrl+V para colar diretamente na caixa.');
    }
}

function limparTextoTranscricao() {
    const textareaResultado = document.getElementById('texto-resultado-trns');
    if (!textareaResultado) return;
    textareaResultado.value = '';
    atualizarContadorTextoTrns();
    mostrarToast('Caixa de texto limpa.');
}

function atualizarContadorTextoTrns() {
    const textareaResultado = document.getElementById('texto-resultado-trns');
    const contadorEl = document.getElementById('contador-texto-trns');
    if (!textareaResultado || !contadorEl) return;

    const val = textareaResultado.value || '';
    const chars = val.length;
    const words = val.trim() ? val.trim().split(/\s+/).length : 0;

    contadorEl.textContent = `${words} palavra${words === 1 ? '' : 's'} · ${chars} caractere${chars === 1 ? '' : 's'}`;
}
