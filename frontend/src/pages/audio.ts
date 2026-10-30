import { baixarResultado, Cancelado, criarCancelamento, executarFerramenta, type Progresso, type StatusJob } from '../lib/api';
import { baixar, delegar, formatarTamanho, porId, valor } from '../lib/dom';
import { t } from '../lib/i18n';
import { mostrarToast } from '../lib/toast';

const ENDPOINTS: Record<string, string> = {
  conv: '/api/converter', cut: '/api/cortar', vol: '/api/volume', spd: '/api/velocidade',
  rev: '/api/inverter', join: '/api/juntar', trns: '/api/transcrever',
};
const EXTENSOES_JUNTAR = ['mp3', 'wav', 'aac', 'ogg', 'flac', 'm4a', 'opus', 'wma'];

const selecionados = new Map<string, File>();
const faixas: File[] = [];
let urlPreviewCorte: string | null = null;

// ── Execução ──────────────────────────────────────────────────
function progressoDe(id: string): Progresso & { encerrar(): void } {
  const area = porId(`progress-${id}`);
  const barra = porId(`fill-${id}`);
  const rotulo = porId(`label-${id}`);
  const pct = porId(`pct-${id}`);
  area?.classList.add('visivel');
  return {
    atualizar(percent, texto) {
      if (barra) barra.style.width = `${percent ?? 30}%`;
      if (rotulo) rotulo.textContent = texto;
      if (pct) pct.textContent = percent === null ? '' : `${Math.round(percent)}%`;
    },
    encerrar() {
      area?.classList.remove('visivel');
      if (barra) barra.style.width = '0%';
    },
  };
}

function mostrarErro(id: string, mensagem: string): void {
  porId(`erro-${id}`)?.classList.add('visivel', 'erro');
  const texto = porId(`erro-msg-${id}`);
  if (texto) texto.textContent = mensagem;
  mostrarToast(mensagem, true);
}

function limparErro(id: string): void {
  porId(`erro-${id}`)?.classList.remove('visivel', 'erro');
}

function executar(id: string, dados: FormData, aoConcluir: (st: StatusJob) => void): void {
  const botao = porId<HTMLButtonElement>(`btn-${id}`);
  if (!botao || botao.disabled) return;
  const original = botao.innerHTML;
  limparErro(id);
  botao.disabled = true;
  botao.innerHTML = `<span>${t('job.processing')}</span><div class="spinner"></div>`;
  const progresso = progressoDe(id);
  const cancelamento = criarCancelamento(porId(`progress-${id}`));

  executarFerramenta(ENDPOINTS[id] ?? '', dados, progresso, cancelamento.sinal)
    .then(aoConcluir)
    .catch((erro: unknown) => {
      if (erro instanceof Cancelado) mostrarToast(t('job.canceled'));
      else mostrarErro(id, erro instanceof Error ? erro.message : t('job.conn_err'));
    })
    .finally(() => {
      cancelamento.remover();
      progresso.encerrar();
      botao.disabled = false;
      botao.innerHTML = original;
    });
}

function concluirComDownload(st: StatusJob): void {
  baixarResultado(st);
  mostrarToast(st.aviso ?? t('job.done'));
}

function rodarFerramenta(id: string): void {
  const arquivo = selecionados.get(id);
  if (!arquivo) {
    mostrarErro(id, t('job.select_file'));
    return;
  }
  const dados = new FormData();
  dados.append('arquivo', arquivo);
  if (id === 'conv') {
    dados.append('formato', valor('formato-conv', 'mp3'));
    dados.append('bitrate', valor('bitrate-conv', '192k'));
    dados.append('canais', valor('channels-conv', '2'));
    dados.append('sample_rate', valor('sample-conv', '44100'));
  } else if (id === 'cut') {
    dados.append('inicio', valor('inicio-cut', '0'));
    dados.append('fim', valor('fim-cut'));
  } else if (id === 'vol') {
    dados.append('ajuste', valor('ajuste-vol', '+6'));
  } else if (id === 'spd') {
    dados.append('fator', valor('fator-spd', '1.5'));
  }
  executar(id, dados, concluirComDownload);
}

function rodarJuncao(): void {
  if (faixas.length < 2) {
    mostrarErro('join', t('job.select_two'));
    return;
  }
  const dados = new FormData();
  for (const faixa of faixas) dados.append('arquivos', faixa);
  dados.append('formato', valor('formato-join', 'mp3'));
  dados.append('bitrate', valor('bitrate-join', '192k'));
  executar('join', dados, concluirComDownload);
}

function rodarTranscricao(): void {
  const arquivo = selecionados.get('trns');
  if (!arquivo) {
    mostrarErro('trns', t('job.select_file'));
    return;
  }
  const dados = new FormData();
  dados.append('arquivo', arquivo);
  dados.append('idioma', valor('idioma-trns', 'auto'));
  dados.append('formato', valor('formato-trns', 'txt'));
  dados.append('modelo', valor('modelo-trns', 'small'));
  const previa = porId('wrap-preview-trns');
  if (previa) previa.style.display = 'flex';
  executar('trns', dados, (st) => {
    const caixa = porId<HTMLTextAreaElement>('texto-resultado-trns');
    if (caixa) caixa.value = String(st.dados?.texto ?? '');
    atualizarContador();
    concluirComDownload(st);
  });
}

// ── Seleção de arquivos ───────────────────────────────────────
function aoSelecionar(id: string, arquivo: File): void {
  selecionados.set(id, arquivo);
  const info = `${arquivo.name} (${formatarTamanho(arquivo.size)})`;
  porId(`upload-${id}`)?.classList.add('tem-arquivo');
  const status = porId(`status-${id}`);
  if (status) {
    status.removeAttribute('data-i18n');
    status.textContent = info;
    status.classList.add('tem-arquivo');
  }
  limparErro(id);
  if (id === 'cut') carregarPreviewCorte(arquivo);
}

function adicionarFaixa(arquivo: File): void {
  const ext = arquivo.name.split('.').pop()?.toLowerCase() ?? '';
  if (!EXTENSOES_JUNTAR.includes(ext)) {
    mostrarToast(`${t('file.ignored')}: ${arquivo.name}`, true);
    return;
  }
  faixas.push(arquivo);
  renderizarFaixas();
  limparErro('join');
}

function renderizarFaixas(): void {
  const lista = porId('files-list-join');
  const vazio = porId('empty-join');
  if (!lista) return;
  Array.from(lista.children).forEach((filho) => {
    if (filho !== vazio) filho.remove();
  });
  if (vazio) vazio.style.display = faixas.length ? 'none' : 'block';
  faixas.forEach((arquivo, i) => {
    const item = document.createElement('div');
    item.className = 'file-item';
    const num = document.createElement('span');
    num.className = 'file-item-num';
    num.textContent = String(i + 1).padStart(2, '0');
    const nome = document.createElement('span');
    nome.className = 'file-item-name';
    nome.title = arquivo.name;
    nome.textContent = arquivo.name;
    const tamanho = document.createElement('span');
    tamanho.className = 'file-item-size';
    tamanho.textContent = formatarTamanho(arquivo.size);
    const remover = document.createElement('button');
    remover.className = 'file-item-remove';
    remover.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
    remover.addEventListener('click', () => {
      faixas.splice(i, 1);
      renderizarFaixas();
    });
    item.append(num, nome, tamanho, remover);
    lista.appendChild(item);
  });
}

// ── Corte com prévia ──────────────────────────────────────────
function segundosParaTexto(segundos: number): string {
  if (Number.isNaN(segundos) || segundos < 0) return '0:00';
  return `${Math.floor(segundos / 60)}:${String(Math.floor(segundos % 60)).padStart(2, '0')}`;
}

function textoParaSegundos(texto: string): number {
  const partes = texto.trim().split(':');
  if (partes.length === 2) return (Number.parseInt(partes[0] ?? '', 10) || 0) * 60 + (Number.parseFloat(partes[1] ?? '') || 0);
  return Number.parseFloat(texto) || 0;
}

function carregarPreviewCorte(arquivo: File): void {
  const audio = porId<HTMLAudioElement>('audio-preview-cut');
  const inicio = porId<HTMLInputElement>('slider-inicio-cut');
  const fim = porId<HTMLInputElement>('slider-fim-cut');
  if (!audio || !inicio || !fim) return;
  if (urlPreviewCorte) URL.revokeObjectURL(urlPreviewCorte);
  urlPreviewCorte = URL.createObjectURL(arquivo);
  audio.src = urlPreviewCorte;

  audio.onloadedmetadata = () => {
    const duracao = audio.duration;
    if (!duracao || Number.isNaN(duracao)) return;
    inicio.disabled = fim.disabled = false;
    inicio.min = fim.min = '0';
    inicio.max = fim.max = String(duracao);
    inicio.value = '0';
    fim.value = String(duracao);
    const texto = segundosParaTexto(duracao);
    for (const [id, conteudo] of [['preview-total-cut', texto], ['badge-inicio-cut', '0:00'], ['badge-fim-cut', texto], ['duracao-cut-valor', texto]] as const) {
      const el = porId(id);
      if (el) el.textContent = conteudo;
    }
    const campoInicio = porId<HTMLInputElement>('inicio-cut');
    const campoFim = porId<HTMLInputElement>('fim-cut');
    if (campoInicio) campoInicio.value = '0:00';
    if (campoFim) campoFim.value = texto;
    const area = porId('cut-interactive-wrap');
    if (area) area.style.display = 'flex';
    const duracaoArea = porId('duracao-cut-wrap');
    if (duracaoArea) duracaoArea.style.display = 'block';
  };
  audio.ontimeupdate = () => {
    const atual = porId('preview-curr-cut');
    if (atual) atual.textContent = segundosParaTexto(audio.currentTime);
    if (audio.currentTime >= (Number.parseFloat(fim.value) || audio.duration)) {
      audio.pause();
      audio.currentTime = Number.parseFloat(inicio.value) || 0;
      atualizarIconePreview(false);
    }
  };
}

function aoMoverSlider(tipo: string): void {
  const audio = porId<HTMLAudioElement>('audio-preview-cut');
  const inicio = porId<HTMLInputElement>('slider-inicio-cut');
  const fim = porId<HTMLInputElement>('slider-fim-cut');
  if (!inicio || !fim) return;
  let a = Number.parseFloat(inicio.value) || 0;
  let b = Number.parseFloat(fim.value) || audio?.duration || 100;
  if (tipo === 'inicio') {
    if (a >= b) {
      a = Math.max(0, b - 0.5);
      inicio.value = String(a);
    }
    const badge = porId('badge-inicio-cut');
    if (badge) badge.textContent = segundosParaTexto(a);
    const campo = porId<HTMLInputElement>('inicio-cut');
    if (campo) campo.value = segundosParaTexto(a);
    if (audio && !audio.paused) audio.currentTime = a;
  } else {
    if (b <= a) {
      b = Math.min(Number.parseFloat(fim.max), a + 0.5);
      fim.value = String(b);
    }
    const badge = porId('badge-fim-cut');
    if (badge) badge.textContent = segundosParaTexto(b);
    const campo = porId<HTMLInputElement>('fim-cut');
    if (campo) campo.value = segundosParaTexto(b);
  }
}

function aoDigitarTempo(tipo: string): void {
  const slider = porId<HTMLInputElement>(`slider-${tipo}-cut`);
  const campo = porId<HTMLInputElement>(`${tipo}-cut`);
  if (!slider || !campo) return;
  const segundos = textoParaSegundos(campo.value);
  if (segundos >= 0 && segundos <= Number.parseFloat(slider.max)) {
    slider.value = String(segundos);
    const badge = porId(`badge-${tipo}-cut`);
    if (badge) badge.textContent = segundosParaTexto(segundos);
  }
}

function atualizarIconePreview(tocando: boolean): void {
  const play = porId('icon-play-cut');
  const pausa = porId('icon-pause-cut');
  const rotulo = porId('label-play-preview-cut');
  if (play) play.style.display = tocando ? 'none' : 'inline';
  if (pausa) pausa.style.display = tocando ? 'inline' : 'none';
  if (rotulo) {
    rotulo.removeAttribute('data-i18n');
    rotulo.textContent = tocando ? t('cut.pause') : t('cut.play');
  }
}

function alternarPreview(): void {
  const audio = porId<HTMLAudioElement>('audio-preview-cut');
  if (!audio?.getAttribute('src')) {
    porId('arquivo-cut')?.click();
    return;
  }
  if (!audio.paused) {
    audio.pause();
    atualizarIconePreview(false);
    return;
  }
  const a = Number.parseFloat(porId<HTMLInputElement>('slider-inicio-cut')?.value ?? '') || 0;
  const b = Number.parseFloat(porId<HTMLInputElement>('slider-fim-cut')?.value ?? '') || audio.duration;
  if (audio.currentTime < a || audio.currentTime >= b) audio.currentTime = a;
  void audio.play().then(() => atualizarIconePreview(true)).catch(() => undefined);
}

// ── Transcrição: caixa de texto ───────────────────────────────
function caixaTexto(): HTMLTextAreaElement | null {
  return porId<HTMLTextAreaElement>('texto-resultado-trns');
}

function atualizarContador(): void {
  const contador = porId('contador-texto-trns');
  const texto = caixaTexto()?.value ?? '';
  if (!contador) return;
  const palavras = texto.trim() ? texto.trim().split(/\s+/).length : 0;
  contador.textContent = `${palavras} ${t('trns.words')} · ${texto.length} ${t('trns.chars')}`;
}

function iniciarAcoesDeTexto(): void {
  delegar('click', '[data-action="trns-copiar"]', () => {
    const texto = caixaTexto()?.value;
    if (texto) void navigator.clipboard.writeText(texto).then(() => mostrarToast(t('trns.copied')));
  });
  delegar('click', '[data-action="trns-colar"]', () => {
    navigator.clipboard.readText().then((texto) => {
      const caixa = caixaTexto();
      if (caixa && texto) {
        caixa.value = texto;
        atualizarContador();
        mostrarToast(t('trns.pasted'));
      }
    }).catch(() => {
      caixaTexto()?.focus();
      mostrarToast(t('trns.paste_hint'));
    });
  });
  delegar('click', '[data-action="trns-limpar"]', () => {
    const caixa = caixaTexto();
    if (caixa) caixa.value = '';
    atualizarContador();
    mostrarToast(t('trns.cleared'));
  });
  delegar('click', '[data-action="trns-baixar"]', () => {
    const texto = caixaTexto()?.value;
    if (!texto) {
      mostrarToast(t('trns.empty'), true);
      return;
    }
    const url = URL.createObjectURL(new Blob([texto], { type: 'text/plain;charset=utf-8' }));
    baixar(url, `transcricao_prisma.${valor('formato-trns', 'txt')}`);
    URL.revokeObjectURL(url);
  });
}

function atualizarResumoConversao(): void {
  const mono = valor('channels-conv', '2') === '1';
  const taxa = valor('sample-conv', '44100') === '48000' ? '48.0 kHz' : '44.1 kHz';
  const resumo = porId('hud-sample-display');
  if (resumo) resumo.textContent = `${taxa} · ${mono ? 'Mono' : 'Estéreo'} (${valor('bitrate-conv', '192k')})`;
}

function iniciarArrastar(): void {
  document.querySelectorAll<HTMLElement>('[id^="upload-"], .upload-multi-zone').forEach((zona) => {
    const juntar = zona.classList.contains('upload-multi-zone') || zona.id === 'upload-join';
    const id = zona.id.replace('upload-', '');
    zona.addEventListener('dragover', (e) => {
      e.preventDefault();
      zona.classList.add('drag-over');
    });
    zona.addEventListener('dragleave', () => zona.classList.remove('drag-over'));
    zona.addEventListener('drop', (e) => {
      e.preventDefault();
      zona.classList.remove('drag-over');
      const arquivos = Array.from(e.dataTransfer?.files ?? []);
      if (juntar) arquivos.forEach(adicionarFaixa);
      else if (arquivos[0]) aoSelecionar(id, arquivos[0]);
    });
  });
}

export function iniciarAudio(): void {
  delegar('change', '[data-file-tool]', (el) => {
    const arquivo = (el as HTMLInputElement).files?.[0];
    if (arquivo) aoSelecionar(el.dataset.fileTool ?? '', arquivo);
  });
  delegar('change', '[data-file-join]', (el) => {
    const entrada = el as HTMLInputElement;
    Array.from(entrada.files ?? []).forEach(adicionarFaixa);
    entrada.value = '';
  });
  delegar('click', '[data-action="audio-run"]', (el) => rodarFerramenta(el.dataset.tool ?? ''));
  delegar('click', '[data-action="audio-join"]', rodarJuncao);
  delegar('click', '[data-action="audio-transcrever"]', rodarTranscricao);
  delegar('click', '[data-action="cut-preview"]', alternarPreview);
  delegar('input', '[data-cut-slider]', (el) => aoMoverSlider(el.dataset.cutSlider ?? ''));
  delegar('input', '[data-cut-text]', (el) => aoDigitarTempo(el.dataset.cutText ?? ''));
  delegar('input', '[data-trns-contador]', atualizarContador);
  delegar('input', '[data-speed]', (el) => {
    const mostrador = porId('valor-spd');
    if (mostrador) mostrador.textContent = `${Number.parseFloat((el as HTMLInputElement).value).toFixed(2)}×`;
  });
  document.addEventListener('chipAlterado', atualizarResumoConversao);
  iniciarAcoesDeTexto();
  iniciarArrastar();
  atualizarContador();
}
