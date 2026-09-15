/**
 * static/video_script.js — Lógica das Ferramentas de Vídeo no Prisma Audio
 */

document.addEventListener('DOMContentLoaded', () => {
    initVideoDragAndDrop();
});


function initVideoDragAndDrop() {
    setupDz('dz-v2a', 'input-v2a', (file) => onVideoSelected(file, 'status-v2a'));
    setupDz('dz-v2g', 'input-v2g', (file) => {
        const input = document.getElementById('input-v2g');
        const dt = new DataTransfer();
        dt.items.add(file);
        input.files = dt.files;
        onVideoGifSelected(input);
    });
    setupDz('upload-vconv', 'input-vconv', (file) => onVideoSelected(file, 'status-vconv'));
    setupDz('upload-vcomp', 'input-vcomp', (file) => onVideoSelected(file, 'status-vcomp'));
    setupDz('upload-vmute', 'input-vmute', (file) => onVideoSelected(file, 'status-vmute'));
    setupDz('upload-vsnap', 'input-vsnap', (file) => onVideoSelected(file, 'status-vsnap'));
}

function setupDz(dzId, inputId, onFile) {
    const dz = document.getElementById(dzId);
    if (!dz) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dz.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dz.addEventListener(eventName, () => dz.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dz.addEventListener(eventName, () => dz.classList.remove('dragover'), false);
    });

    dz.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            onFile(files[0]);
        }
    });
}

function onVideoSelected(inputOrFile, statusId) {
    const file = inputOrFile.files ? inputOrFile.files[0] : inputOrFile;
    const statusEl = document.getElementById(statusId);
    if (!statusEl) return;

    if (file) {
        statusEl.textContent = `✓ Selecionado: ${file.name} (${formatarTamanhoBytes(file.size)})`;
        statusEl.classList.add('tem-arquivo');
    } else {
        statusEl.textContent = 'Nenhum vídeo selecionado';
        statusEl.classList.remove('tem-arquivo');
    }
}

function onVideoGifSelected(input) {
    const file = input.files ? input.files[0] : null;
    const statusEl = document.getElementById('status-v2g');
    const previewWrapper = document.getElementById('wrapper-preview-gif');
    const videoPreview = document.getElementById('video-preview-gif');
    const durationInput = document.getElementById('gif-duration');

    if (!file) {
        if (statusEl) {
            statusEl.textContent = 'Nenhum vídeo selecionado';
            statusEl.classList.remove('tem-arquivo');
        }
        if (previewWrapper) previewWrapper.style.display = 'none';
        return;
    }

    if (statusEl) {
        statusEl.textContent = `✓ Selecionado: ${file.name} (${formatarTamanhoBytes(file.size)})`;
        statusEl.classList.add('tem-arquivo');
    }


    // Carregar preview em vídeo
    const videoUrl = URL.createObjectURL(file);
    if (videoPreview) {
        videoPreview.src = videoUrl;
        videoPreview.onloadedmetadata = () => {
            if (durationInput && (!durationInput.value || parseFloat(durationInput.value) > videoPreview.duration)) {
                durationInput.value = Math.min(5, Math.floor(videoPreview.duration));
            }
        };
        if (previewWrapper) previewWrapper.style.display = 'block';
    }
}

function formatarTamanhoBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function obterCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

function mostrarToast(msg, ehErro = false) {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toastMsg');
    if (!toast || !toastMsg) return;

    toastMsg.textContent = msg;
    if (ehErro) {
        toast.style.borderColor = '#ff4d4d';
        toast.querySelector('.toast-icone').textContent = '✕';
        toast.querySelector('.toast-icone').style.color = '#ff4d4d';
    } else {
        toast.style.borderColor = 'var(--accent)';
        toast.querySelector('.toast-icone').textContent = '✓';
        toast.querySelector('.toast-icone').style.color = 'var(--accent)';
    }

    toast.classList.add('visivel');
    setTimeout(() => {
        toast.classList.remove('visivel');
    }, 4000);
}

function dispararDownloadAutomatico(urlDownload, nomeDownload) {
    if (!urlDownload) return;
    try {
        const a = document.createElement('a');
        a.href = urlDownload;
        if (nomeDownload) a.download = nomeDownload;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    } catch (e) {
        console.warn('Erro ao disparar download automático:', e);
    }
}

// ── 1. MP4 PARA MP3 ──────────────────────────────────────────
async function executarMp4ParaMp3() {
    const fileInput = document.getElementById('input-v2a');
    const bitrateSelect = document.getElementById('bitrate-v2a');
    const btn = document.getElementById('btn-v2a');
    const progressWrap = document.getElementById('progress-v2a');
    const fillBar = document.getElementById('fill-v2a');
    const labelProgress = document.getElementById('label-v2a');
    const resBox = document.getElementById('resultado-v2a');

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        mostrarToast('Selecione um arquivo de vídeo primeiro.', true);
        return;
    }

    const formData = new FormData();
    formData.append('arquivo', fileInput.files[0]);
    formData.append('bitrate', bitrateSelect ? bitrateSelect.value : '192k');

    btn.disabled = true;
    resBox.style.display = 'none';
    progressWrap.style.display = 'block';
    fillBar.style.width = '20%';
    labelProgress.textContent = 'Extraindo áudio MP3 do vídeo...';

    try {
        let prog = 20;
        const interval = setInterval(() => {
            prog = Math.min(prog + 10, 85);
            fillBar.style.width = `${prog}%`;
        }, 400);

        const resp = await fetch('/api/video/mp4-para-mp3', {
            method: 'POST',
            headers: { 'X-CSRFToken': obterCsrfToken() },
            body: formData
        });

        clearInterval(interval);
        fillBar.style.width = '100%';

        const data = await resp.json();
        btn.disabled = false;
        setTimeout(() => progressWrap.style.display = 'none', 500);

        if (resp.ok && data.ok) {
            mostrarToast('Áudio MP3 extraído com sucesso!');
            resBox.innerHTML = `
                <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px;">
                    <div>
                        <strong style="color:var(--text);">${data.nome_download}</strong>
                        <span style="display:block; font-size:12px; color:var(--muted2); font-family:var(--mono); margin-top:2px;">Tamanho: ${data.tamanho}</span>
                    </div>
                </div>
            `;
            resBox.style.display = 'block';
            dispararDownloadAutomatico(data.url_download, data.nome_download);
        } else {
            mostrarToast(data.erro || 'Erro ao converter para MP3', true);
        }
    } catch (err) {
        btn.disabled = false;
        progressWrap.style.display = 'none';
        mostrarToast('Erro de conexão com o servidor.', true);
    }
}

// ── 2. MP4 PARA GIF ──────────────────────────────────────────
async function executarMp4ParaGif() {
    const fileInput = document.getElementById('input-v2g');
    const startInput = document.getElementById('gif-start');
    const durInput = document.getElementById('gif-duration');
    const fpsSelect = document.getElementById('gif-fps');
    const widthSelect = document.getElementById('gif-width');

    const btn = document.getElementById('btn-v2g');
    const progressWrap = document.getElementById('progress-v2g');
    const fillBar = document.getElementById('fill-v2g');
    const labelProgress = document.getElementById('label-v2g');
    const resBox = document.getElementById('resultado-v2g');

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        mostrarToast('Selecione um arquivo de vídeo primeiro.', true);
        return;
    }

    const formData = new FormData();
    formData.append('arquivo', fileInput.files[0]);
    formData.append('inicio', startInput ? startInput.value : '0');
    formData.append('duracao', durInput ? durInput.value : '');
    formData.append('fps', fpsSelect ? fpsSelect.value : '10');
    formData.append('largura', widthSelect ? widthSelect.value : '480');

    btn.disabled = true;
    resBox.style.display = 'none';
    progressWrap.style.display = 'block';
    fillBar.style.width = '15%';
    labelProgress.textContent = 'Gerando paleta de cores e renderizando GIF...';

    try {
        let prog = 15;
        const interval = setInterval(() => {
            prog = Math.min(prog + 8, 90);
            fillBar.style.width = `${prog}%`;
        }, 500);

        const resp = await fetch('/api/video/mp4-para-gif', {
            method: 'POST',
            headers: { 'X-CSRFToken': obterCsrfToken() },
            body: formData
        });

        clearInterval(interval);
        fillBar.style.width = '100%';

        const data = await resp.json();
        btn.disabled = false;
        setTimeout(() => progressWrap.style.display = 'none', 500);

        if (resp.ok && data.ok) {
            mostrarToast('GIF animado gerado com sucesso!');
            resBox.innerHTML = `
                <div style="display:flex; flex-direction:column; gap:16px;">
                    <div style="text-align:center;">
                        <img src="${data.url_download}" alt="GIF Gerado" style="max-width:100%; max-height:300px; border-radius:6px; border:1px solid var(--border2); box-shadow: 0 4px 16px rgba(0,0,0,0.2);">
                    </div>
                    <div>
                        <strong style="color:var(--text);">${data.nome_download}</strong>
                        <span style="display:block; font-size:12px; color:var(--muted2); font-family:var(--mono); margin-top:2px;">Tamanho: ${data.tamanho}</span>
                    </div>
                </div>
            `;
            resBox.style.display = 'block';
            dispararDownloadAutomatico(data.url_download, data.nome_download);
        } else {
            mostrarToast(data.erro || 'Erro ao converter para GIF', true);
        }
    } catch (err) {
        btn.disabled = false;
        progressWrap.style.display = 'none';
        mostrarToast('Erro de conexão com o servidor.', true);
    }
}

// ── 3. BAIXAR VÍDEOS POR LINK ────────────────────────────────
async function executarBaixarLink() {
    const urlInput = document.getElementById('input-url-dl');
    const formatoSelect = document.getElementById('formato-dl');
    const qualidadeSelect = document.getElementById('qualidade-dl');

    const btn = document.getElementById('btn-dl');
    const progressWrap = document.getElementById('progress-dl');
    const fillBar = document.getElementById('fill-dl');
    const labelProgress = document.getElementById('label-dl');
    const pctEl = document.getElementById('pct-dl');
    const resBox = document.getElementById('resultado-dl');

    const url = urlInput ? urlInput.value.trim() : '';

    if (!url) {
        mostrarToast('Cole uma URL de vídeo válida.', true);
        return;
    }

    const taskId = 'dl_' + Math.random().toString(36).substring(2) + Date.now();

    const formData = new FormData();
    formData.append('url', url);
    formData.append('formato', formatoSelect ? formatoSelect.value : 'mp4');
    formData.append('qualidade', qualidadeSelect ? qualidadeSelect.value : 'best');
    formData.append('task_id', taskId);

    btn.disabled = true;
    resBox.style.display = 'none';
    progressWrap.style.display = 'block';
    fillBar.style.width = '0%';
    if (pctEl) pctEl.textContent = '0%';
    labelProgress.textContent = 'Iniciando download...';

    let isDone = false;

    // Polling em tempo real do progresso do yt-dlp (0.0% a 100%)
    const pollInterval = setInterval(async () => {
        if (isDone) return;
        try {
            const pollResp = await fetch(`/api/video/progresso/${taskId}`);
            if (pollResp.ok) {
                const prog = await pollResp.json();
                if (prog && prog.pct !== undefined) {
                    const pctVal = Math.min(Math.max(prog.pct, 0), 100);
                    fillBar.style.width = `${pctVal}%`;
                    if (pctEl) pctEl.textContent = prog.pct_str || `${pctVal.toFixed(1)}%`;
                    
                    if (prog.status === 'downloading' && prog.speed) {
                        labelProgress.textContent = `Baixando... ${prog.pct_str} (${prog.speed}${prog.eta ? ' — ETA: ' + prog.eta : ''})`;
                    } else if (prog.status === 'finished') {
                        labelProgress.textContent = 'Finalizando arquivo e aplicando tags...';
                    }
                }
            }
        } catch (e) {
            // Ignorar falhas pontuais de polling
        }
    }, 300);

    try {
        const resp = await fetch('/api/video/baixar-link', {
            method: 'POST',
            headers: { 'X-CSRFToken': obterCsrfToken() },
            body: formData
        });

        isDone = true;
        clearInterval(pollInterval);

        fillBar.style.width = '100%';
        if (pctEl) pctEl.textContent = '100%';

        const data = await resp.json();
        btn.disabled = false;
        setTimeout(() => progressWrap.style.display = 'none', 500);

        if (resp.ok && data.ok) {
            mostrarToast('Vídeo baixado com sucesso!');
            resBox.innerHTML = `
                <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px;">
                    <div>
                        <strong style="color:var(--text);">${data.nome_download}</strong>
                        <span style="display:block; font-size:12px; color:var(--muted2); font-family:var(--mono); margin-top:2px;">Tamanho: ${data.tamanho}</span>
                    </div>
                </div>
            `;
            resBox.style.display = 'block';
            dispararDownloadAutomatico(data.url_download, data.nome_download);
        } else {
            mostrarToast(data.erro || 'Erro ao baixar o vídeo da URL.', true);
        }

    } catch (err) {
        isDone = true;
        clearInterval(pollInterval);
        btn.disabled = false;
        progressWrap.style.display = 'none';
        mostrarToast('Erro ao processar o download.', true);
    }
}

// ── 4. CONVERSOR DE FORMATO ────────────────────────────────────
async function executarConverterFormato() {
    const fileInput = document.getElementById('input-vconv');
    const formatoSelect = document.getElementById('formato-vconv');
    const btn = document.getElementById('btn-vconv');
    const progressWrap = document.getElementById('progress-vconv');
    const fillBar = document.getElementById('fill-vconv');
    const labelProgress = document.getElementById('label-vconv');
    const resBox = document.getElementById('resultado-vconv');

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        mostrarToast('Selecione um arquivo de vídeo primeiro.', true);
        return;
    }

    const formData = new FormData();
    formData.append('arquivo', fileInput.files[0]);
    formData.append('formato', formatoSelect ? formatoSelect.value : 'mp4');

    btn.disabled = true;
    resBox.style.display = 'none';
    progressWrap.style.display = 'block';
    fillBar.style.width = '20%';
    labelProgress.textContent = 'Convertendo formato do vídeo...';

    try {
        let prog = 20;
        const interval = setInterval(() => {
            prog = Math.min(prog + 10, 85);
            fillBar.style.width = `${prog}%`;
        }, 400);

        const resp = await fetch('/api/video/converter-formato', {
            method: 'POST',
            headers: { 'X-CSRFToken': obterCsrfToken() },
            body: formData
        });

        clearInterval(interval);
        fillBar.style.width = '100%';

        const data = await resp.json();
        btn.disabled = false;
        setTimeout(() => progressWrap.style.display = 'none', 500);

        if (resp.ok && data.ok) {
            mostrarToast('Formato convertido com sucesso!');
            resBox.innerHTML = `
                <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px;">
                    <div>
                        <strong style="color:var(--text);">${data.nome_download}</strong>
                        <span style="display:block; font-size:12px; color:var(--muted2); font-family:var(--mono); margin-top:2px;">Tamanho: ${data.tamanho}</span>
                    </div>
                </div>
            `;
            resBox.style.display = 'block';
            dispararDownloadAutomatico(data.url_download, data.nome_download);
        } else {
            mostrarToast(data.erro || 'Erro na conversão de formato', true);
        }
    } catch (err) {
        btn.disabled = false;
        progressWrap.style.display = 'none';
        mostrarToast('Erro de conexão com o servidor.', true);
    }
}

// ── 5. COMPRESSOR DE VÍDEO ──────────────────────────────────────
async function executarCompressorVideo() {
    const fileInput = document.getElementById('input-vcomp');
    const nivelSelect = document.getElementById('nivel-vcomp');
    const btn = document.getElementById('btn-vcomp');
    const progressWrap = document.getElementById('progress-vcomp');
    const fillBar = document.getElementById('fill-vcomp');
    const labelProgress = document.getElementById('label-vcomp');
    const resBox = document.getElementById('resultado-vcomp');

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        mostrarToast('Selecione um arquivo de vídeo primeiro.', true);
        return;
    }

    const formData = new FormData();
    formData.append('arquivo', fileInput.files[0]);
    formData.append('nivel', nivelSelect ? nivelSelect.value : 'whatsapp');

    btn.disabled = true;
    resBox.style.display = 'none';
    progressWrap.style.display = 'block';
    fillBar.style.width = '20%';
    labelProgress.textContent = 'Otimizando e comprimindo vídeo...';

    try {
        let prog = 20;
        const interval = setInterval(() => {
            prog = Math.min(prog + 8, 88);
            fillBar.style.width = `${prog}%`;
        }, 500);

        const resp = await fetch('/api/video/compressor', {
            method: 'POST',
            headers: { 'X-CSRFToken': obterCsrfToken() },
            body: formData
        });

        clearInterval(interval);
        fillBar.style.width = '100%';

        const data = await resp.json();
        btn.disabled = false;
        setTimeout(() => progressWrap.style.display = 'none', 500);

        if (resp.ok && data.ok) {
            mostrarToast('Vídeo comprimido com sucesso!');
            resBox.innerHTML = `
                <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px;">
                    <div>
                        <strong style="color:var(--text);">${data.nome_download}</strong>
                        <span style="display:block; font-size:12px; color:var(--muted2); font-family:var(--mono); margin-top:2px;">Tamanho: ${data.tamanho}</span>
                    </div>
                </div>
            `;
            resBox.style.display = 'block';
            dispararDownloadAutomatico(data.url_download, data.nome_download);
        } else {
            mostrarToast(data.erro || 'Erro ao comprimir vídeo', true);
        }
    } catch (err) {
        btn.disabled = false;
        progressWrap.style.display = 'none';
        mostrarToast('Erro de conexão com o servidor.', true);
    }
}

// ── 6. REMOVER ÁUDIO DO VÍDEO ──────────────────────────────────
async function executarRemoverAudio() {
    const fileInput = document.getElementById('input-vmute');
    const btn = document.getElementById('btn-vmute');
    const progressWrap = document.getElementById('progress-vmute');
    const fillBar = document.getElementById('fill-vmute');
    const labelProgress = document.getElementById('label-vmute');
    const resBox = document.getElementById('resultado-vmute');

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        mostrarToast('Selecione um arquivo de vídeo primeiro.', true);
        return;
    }

    const formData = new FormData();
    formData.append('arquivo', fileInput.files[0]);

    btn.disabled = true;
    resBox.style.display = 'none';
    progressWrap.style.display = 'block';
    fillBar.style.width = '30%';
    labelProgress.textContent = 'Removendo faixa de áudio...';

    try {
        const resp = await fetch('/api/video/remover-audio', {
            method: 'POST',
            headers: { 'X-CSRFToken': obterCsrfToken() },
            body: formData
        });

        fillBar.style.width = '100%';

        const data = await resp.json();
        btn.disabled = false;
        setTimeout(() => progressWrap.style.display = 'none', 500);

        if (resp.ok && data.ok) {
            mostrarToast('Vídeo silenciado com sucesso!');
            resBox.innerHTML = `
                <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px;">
                    <div>
                        <strong style="color:var(--text);">${data.nome_download}</strong>
                        <span style="display:block; font-size:12px; color:var(--muted2); font-family:var(--mono); margin-top:2px;">Tamanho: ${data.tamanho}</span>
                    </div>
                </div>
            `;
            resBox.style.display = 'block';
            dispararDownloadAutomatico(data.url_download, data.nome_download);
        } else {
            mostrarToast(data.erro || 'Erro ao silenciar vídeo', true);
        }
    } catch (err) {
        btn.disabled = false;
        progressWrap.style.display = 'none';
        mostrarToast('Erro de conexão com o servidor.', true);
    }
}

// ── 7. CAPTURAR FOTO DO VÍDEO ──────────────────────────────────
async function executarCapturarFoto() {
    const fileInput = document.getElementById('input-vsnap');
    const timeInput = document.getElementById('tempo-vsnap');
    const formatoSelect = document.getElementById('formato-vsnap');

    const btn = document.getElementById('btn-vsnap');
    const progressWrap = document.getElementById('progress-vsnap');
    const fillBar = document.getElementById('fill-vsnap');
    const labelProgress = document.getElementById('label-vsnap');
    const resBox = document.getElementById('resultado-vsnap');

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        mostrarToast('Selecione um arquivo de vídeo primeiro.', true);
        return;
    }

    const formData = new FormData();
    formData.append('arquivo', fileInput.files[0]);
    formData.append('tempo', timeInput ? timeInput.value : '1.0');
    formData.append('formato', formatoSelect ? formatoSelect.value : 'png');

    btn.disabled = true;
    resBox.style.display = 'none';
    progressWrap.style.display = 'block';
    fillBar.style.width = '35%';
    labelProgress.textContent = 'Extraindo imagem em HD do vídeo...';

    try {
        const resp = await fetch('/api/video/capturar-foto', {
            method: 'POST',
            headers: { 'X-CSRFToken': obterCsrfToken() },
            body: formData
        });

        fillBar.style.width = '100%';

        const data = await resp.json();
        btn.disabled = false;
        setTimeout(() => progressWrap.style.display = 'none', 500);

        if (resp.ok && data.ok) {
            mostrarToast('Foto capturada com sucesso!');
            resBox.innerHTML = `
                <div style="display:flex; flex-direction:column; gap:16px;">
                    <div style="text-align:center;">
                        <img src="${data.url_download}" alt="Foto do Vídeo" style="max-width:100%; max-height:260px; border-radius:6px; border:1px solid var(--border2); box-shadow: 0 4px 16px rgba(0,0,0,0.2);">
                    </div>
                    <div>
                        <strong style="color:var(--text);">${data.nome_download}</strong>
                        <span style="display:block; font-size:12px; color:var(--muted2); font-family:var(--mono); margin-top:2px;">Tamanho: ${data.tamanho}</span>
                    </div>
                </div>
            `;
            resBox.style.display = 'block';
            dispararDownloadAutomatico(data.url_download, data.nome_download);
        } else {
            mostrarToast(data.erro || 'Erro ao capturar foto do vídeo', true);
        }
    } catch (err) {
        btn.disabled = false;
        progressWrap.style.display = 'none';
        mostrarToast('Erro de conexão com o servidor.', true);
    }
}

function selecionarFormatoDl(formato, el) {
    const containerFormato = document.getElementById('chips-formato-dl');
    if (containerFormato) {
        containerFormato.querySelectorAll('.opcao-chip').forEach(c => c.classList.remove('selecionado'));
    }
    if (el) el.classList.add('selecionado');

    const inputFormato = document.getElementById('formato-dl');
    if (inputFormato) inputFormato.value = formato;

    const videoChips = document.getElementById('chips-qualidade-video-dl');
    const audioChips = document.getElementById('chips-qualidade-audio-dl');
    const labelQualidade = document.getElementById('label-qualidade-dl');
    const inputQualidade = document.getElementById('qualidade-dl');

    if (formato === 'mp3') {
        if (videoChips) videoChips.style.display = 'none';
        if (audioChips) {
            audioChips.style.display = 'flex';
            let selAudio = audioChips.querySelector('.opcao-chip.selecionado');
            if (!selAudio) {
                selAudio = audioChips.querySelector('.opcao-chip');
                if (selAudio) selAudio.classList.add('selecionado');
            }
            if (inputQualidade && selAudio) {
                inputQualidade.value = selAudio.getAttribute('data-val') || '320k';
            }
        }
        if (labelQualidade) {
            labelQualidade.setAttribute('data-i18n', 'video.dl.quality_audio');
            labelQualidade.textContent = (window.i18n && typeof window.i18n.t === 'function') 
                ? window.i18n.t('video.dl.quality_audio') 
                : 'QUALIDADE DO ÁUDIO';
        }
    } else {
        if (videoChips) {
            videoChips.style.display = 'flex';
            let selVideo = videoChips.querySelector('.opcao-chip.selecionado');
            if (!selVideo) {
                selVideo = videoChips.querySelector('.opcao-chip');
                if (selVideo) selVideo.classList.add('selecionado');
            }
            if (inputQualidade && selVideo) {
                inputQualidade.value = selVideo.getAttribute('data-val') || 'best';
            }
        }
        if (audioChips) audioChips.style.display = 'none';
        if (labelQualidade) {
            labelQualidade.setAttribute('data-i18n', 'video.dl.quality');
            labelQualidade.textContent = (window.i18n && typeof window.i18n.t === 'function') 
                ? window.i18n.t('video.dl.quality') 
                : 'QUALIDADE DE VÍDEO';
        }
    }
}

function selecionarQualidadeDl(qualidade, el) {
    if (!el) return;
    const parent = el.closest('.opcoes-chips');
    if (parent) {
        parent.querySelectorAll('.opcao-chip').forEach(c => c.classList.remove('selecionado'));
    }
    el.classList.add('selecionado');

    const input = document.getElementById('qualidade-dl');
    if (input) input.value = qualidade;
}

window.selecionarFormatoDl = selecionarFormatoDl;
window.selecionarQualidadeDl = selecionarQualidadeDl;
window.selecionarChip = window.selecionarChip || function(inputId, valor, chipEl) {
    if (!chipEl) return;
    const parent = chipEl.closest('.opcoes-chips');
    if (parent) {
        parent.querySelectorAll('.opcao-chip').forEach(c => c.classList.remove('selecionado'));
    }
    chipEl.classList.add('selecionado');
    const input = document.getElementById(inputId);
    if (input) input.value = valor;
};
