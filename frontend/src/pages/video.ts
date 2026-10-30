import { baixarResultado, Cancelado, criarCancelamento, executarFerramenta, type StatusJob } from '../lib/api';
import { delegar, formatarTamanho, porId, valor } from '../lib/dom';
import { t } from '../lib/i18n';
import { mostrarToast } from '../lib/toast';

interface Ferramenta {
  url: string;
  entrada?: string;
  /** campo do formulário → id do elemento com o valor */
  campos: Record<string, string>;
  /** Mostra o resultado como imagem na tela */
  imagem?: boolean;
}

const FERRAMENTAS: Record<string, Ferramenta> = {
  v2a: { url: '/api/video/mp4-para-mp3', entrada: 'input-v2a', campos: { bitrate: 'bitrate-v2a' } },
  v2g: { url: '/api/video/mp4-para-gif', entrada: 'input-v2g', campos: { inicio: 'gif-start', duracao: 'gif-duration', fps: 'gif-fps', largura: 'gif-width' }, imagem: true },
  vconv: { url: '/api/video/converter', entrada: 'input-vconv', campos: { formato: 'formato-vconv' } },
  vcomp: { url: '/api/video/compressor', entrada: 'input-vcomp', campos: { nivel: 'nivel-vcomp' } },
  vmute: { url: '/api/video/remover-audio', entrada: 'input-vmute', campos: {} },
  vsnap: { url: '/api/video/capturar-foto', entrada: 'input-vsnap', campos: { tempo: 'tempo-vsnap', formato: 'formato-vsnap' }, imagem: true },
  dl: { url: '/api/video/baixar-link', campos: { url: 'input-url-dl', formato: 'formato-dl', qualidade: 'qualidade-dl' } },
};

function mostrarResultado(id: string, st: StatusJob, comImagem: boolean): void {
  const caixa = porId(`resultado-${id}`);
  if (!caixa) return;
  caixa.replaceChildren();
  // Em "download único" o arquivo some após a primeira leitura: não dá para pré-visualizar.
  if (comImagem && st.download_url && document.body.dataset.retentionPolicy !== 'instant') {
    const img = document.createElement('img');
    img.src = st.download_url;
    img.alt = st.nome_download;
    img.className = 'resultado-imagem';
    caixa.appendChild(img);
  }
  const nome = document.createElement('strong');
  nome.className = 'resultado-nome';
  nome.textContent = st.nome_download;
  const tamanho = document.createElement('span');
  tamanho.className = 'resultado-tamanho';
  tamanho.textContent = `${t('job.size')}: ${st.tamanho ?? ''}`;
  caixa.append(nome, tamanho);
  caixa.style.display = 'block';
}

function rodar(id: string): void {
  const ferramenta = FERRAMENTAS[id];
  const botao = porId<HTMLButtonElement>(`btn-${id}`);
  if (!ferramenta || !botao || botao.disabled) return;

  const dados = new FormData();
  if (ferramenta.entrada) {
    const arquivo = porId<HTMLInputElement>(ferramenta.entrada)?.files?.[0];
    if (!arquivo) {
      mostrarToast(t('job.select_file'), true);
      return;
    }
    dados.append('arquivo', arquivo);
  } else if (!valor('input-url-dl').trim()) {
    mostrarToast(t('job.paste_url'), true);
    return;
  }
  for (const [campo, elemento] of Object.entries(ferramenta.campos)) dados.append(campo, valor(elemento));

  const area = porId(`progress-${id}`);
  const barra = porId(`fill-${id}`);
  const rotulo = porId(`label-${id}`);
  const pct = porId(`pct-${id}`);
  const resultado = porId(`resultado-${id}`);
  botao.disabled = true;
  if (resultado) resultado.style.display = 'none';
  if (area) area.style.display = 'block';
  const cancelamento = criarCancelamento(area);

  executarFerramenta(ferramenta.url, dados, {
    atualizar(percent, texto) {
      if (barra) barra.style.width = `${percent ?? 30}%`;
      if (rotulo) rotulo.textContent = texto;
      if (pct) pct.textContent = percent === null ? '' : `${Math.round(percent)}%`;
    },
  }, cancelamento.sinal)
    .then((st) => {
      mostrarResultado(id, st, ferramenta.imagem === true);
      baixarResultado(st);
      mostrarToast(st.aviso ?? t('job.done'));
    })
    .catch((erro: unknown) => {
      if (erro instanceof Cancelado) mostrarToast(t('job.canceled'));
      else mostrarToast(erro instanceof Error ? erro.message : t('job.conn_err'), true);
    })
    .finally(() => {
      cancelamento.remover();
      botao.disabled = false;
      if (area) area.style.display = 'none';
      if (barra) barra.style.width = '0%';
    });
}

function mostrarSelecionado(idStatus: string, arquivo: File | undefined): void {
  const status = porId(idStatus);
  if (!status) return;
  status.removeAttribute('data-i18n');
  status.textContent = arquivo ? `✓ ${t('file.selected')}: ${arquivo.name} (${formatarTamanho(arquivo.size)})` : t('file.none');
  status.classList.toggle('tem-arquivo', !!arquivo);
}

function aoSelecionarGif(entrada: HTMLInputElement): void {
  const arquivo = entrada.files?.[0];
  mostrarSelecionado('status-v2g', arquivo);
  const area = porId('wrapper-preview-gif');
  const video = porId<HTMLVideoElement>('video-preview-gif');
  const duracao = porId<HTMLInputElement>('gif-duration');
  if (!arquivo || !video) {
    if (area) area.style.display = 'none';
    return;
  }
  if (video.src) URL.revokeObjectURL(video.src);
  video.src = URL.createObjectURL(arquivo);
  video.onloadedmetadata = () => {
    if (duracao && (!duracao.value || Number.parseFloat(duracao.value) > video.duration)) {
      duracao.value = String(Math.min(5, Math.floor(video.duration)));
    }
  };
  if (area) area.style.display = 'block';
}

function selecionarFormatoDownload(el: HTMLElement): void {
  const formato = el.dataset.val ?? 'mp4';
  porId('chips-formato-dl')?.querySelectorAll('.opcao-chip').forEach((c) => c.classList.remove('selecionado'));
  el.classList.add('selecionado');
  const campoFormato = porId<HTMLInputElement>('formato-dl');
  if (campoFormato) campoFormato.value = formato;

  const ehAudio = formato === 'mp3';
  const chipsVideo = porId('chips-qualidade-video-dl');
  const chipsAudio = porId('chips-qualidade-audio-dl');
  if (chipsVideo) chipsVideo.style.display = ehAudio ? 'none' : 'flex';
  if (chipsAudio) chipsAudio.style.display = ehAudio ? 'flex' : 'none';

  const ativos = ehAudio ? chipsAudio : chipsVideo;
  let escolhido = ativos?.querySelector<HTMLElement>('.opcao-chip.selecionado') ?? null;
  if (!escolhido) {
    escolhido = ativos?.querySelector<HTMLElement>('.opcao-chip') ?? null;
    escolhido?.classList.add('selecionado');
  }
  const campoQualidade = porId<HTMLInputElement>('qualidade-dl');
  if (campoQualidade && escolhido) campoQualidade.value = escolhido.dataset.val ?? 'best';
  const rotulo = porId('label-qualidade-dl');
  if (rotulo) {
    rotulo.dataset.i18n = ehAudio ? 'video.dl.quality_audio' : 'video.dl.quality';
    rotulo.textContent = t(ehAudio ? 'video.dl.quality_audio' : 'video.dl.quality');
  }
}

function iniciarArrastar(): void {
  const zonas: Array<[string, string, string]> = [
    ['dz-v2a', 'input-v2a', 'status-v2a'], ['dz-v2g', 'input-v2g', 'status-v2g'],
    ['upload-vconv', 'input-vconv', 'status-vconv'], ['upload-vcomp', 'input-vcomp', 'status-vcomp'],
    ['upload-vmute', 'input-vmute', 'status-vmute'], ['upload-vsnap', 'input-vsnap', 'status-vsnap'],
  ];
  for (const [zonaId, entradaId, statusId] of zonas) {
    const zona = porId(zonaId);
    const entrada = porId<HTMLInputElement>(entradaId);
    if (!zona || !entrada) continue;
    for (const tipo of ['dragenter', 'dragover'] as const) {
      zona.addEventListener(tipo, (e) => {
        e.preventDefault();
        zona.classList.add('dragover');
      });
    }
    zona.addEventListener('dragleave', () => zona.classList.remove('dragover'));
    zona.addEventListener('drop', (e) => {
      e.preventDefault();
      zona.classList.remove('dragover');
      if (!e.dataTransfer?.files.length) return;
      entrada.files = e.dataTransfer.files;
      if (entradaId === 'input-v2g') aoSelecionarGif(entrada);
      else mostrarSelecionado(statusId, entrada.files[0]);
    });
  }
}

export function iniciarVideo(): void {
  delegar('click', '[data-action="video-run"]', (el) => rodar(el.dataset.tool ?? ''));
  delegar('click', '[data-action="dl-format"]', selecionarFormatoDownload);
  delegar('change', '[data-file-status]', (el) => mostrarSelecionado(el.dataset.fileStatus ?? '', (el as HTMLInputElement).files?.[0]));
  delegar('change', '[data-file-gif]', (el) => aoSelecionarGif(el as HTMLInputElement));
  iniciarArrastar();
}
