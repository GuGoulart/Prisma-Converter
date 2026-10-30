import { baixarResultado, Cancelado, criarCancelamento, executarFerramenta } from '../lib/api';
import { formatarTamanho, porId } from '../lib/dom';
import { t } from '../lib/i18n';
import { mostrarToast } from '../lib/toast';

const ORIGENS_ORIENTAVEIS = ['xlsx', 'xls', 'csv', 'json'];

export function iniciarConversor(): void {
  const origem = document.body.dataset.origem ?? '';
  const uid = document.body.dataset.pastaUuid ?? '';
  iniciarUpload();
  iniciarPreview(origem, uid);
  iniciarConversao();
}

function iniciarUpload(): void {
  const caixa = porId('uploadBox');
  const entrada = porId<HTMLInputElement>('arquivo');
  const formulario = porId<HTMLFormElement>('uploadForm');
  const botao = porId<HTMLButtonElement>('btnEnviar');
  if (!caixa || !entrada || !formulario) return;

  const carregando = (): void => {
    if (!botao) return;
    botao.disabled = true;
    botao.innerHTML = `<span>${t('upload.sending')}</span><div class="spinner"></div>`;
  };
  const mostrarArquivo = (): void => {
    const arquivo = entrada.files?.[0];
    if (!arquivo) return;
    const ext = arquivo.name.split('.').pop()?.toLowerCase() ?? '';
    const icone = porId('uploadIcone');
    if (icone) {
      icone.replaceChildren();
      const rotulo = document.createElement('span');
      rotulo.style.cssText = 'font-family:var(--mono);font-size:13px;font-weight:700;color:var(--accent);letter-spacing:.1em;';
      rotulo.textContent = `.${ext}`;
      icone.appendChild(rotulo);
    }
    const titulo = porId('uploadTitulo');
    if (titulo) {
      titulo.removeAttribute('data-i18n');
      titulo.textContent = arquivo.name;
    }
    const descricao = porId('uploadDesc');
    if (descricao) descricao.textContent = `${ext.toUpperCase()} · ${formatarTamanho(arquivo.size)}`;
    caixa.style.borderColor = 'var(--accent)';
  };

  caixa.addEventListener('click', (e) => {
    if (!(e.target instanceof HTMLInputElement)) entrada.click();
  });
  entrada.addEventListener('change', mostrarArquivo);
  formulario.addEventListener('submit', carregando);
  for (const tipo of ['dragenter', 'dragover'] as const) {
    caixa.addEventListener(tipo, (e) => {
      e.preventDefault();
      caixa.classList.add('drag-over');
    });
  }
  caixa.addEventListener('dragleave', () => caixa.classList.remove('drag-over'));
  caixa.addEventListener('drop', (e) => {
    e.preventDefault();
    caixa.classList.remove('drag-over');
    if (!e.dataTransfer?.files.length) return;
    entrada.files = e.dataTransfer.files;
    mostrarArquivo();
    carregando();
    formulario.submit();
  });
}

function destinoSelecionado(): string {
  return document.querySelector<HTMLInputElement>('input[name="destino"]:checked')?.value ?? '';
}

function orientacaoSelecionada(): string {
  return document.querySelector<HTMLInputElement>('input[name="_ori"]:checked')?.value ?? 'retrato';
}

function iniciarPreview(origem: string, uid: string): void {
  const painelOrientacao = porId('orientacaoWrap');
  const campoOrientacao = porId<HTMLInputElement>('orientacaoHidden');

  const ajustarOrientacao = (destino: string): void => {
    painelOrientacao?.classList.toggle('visivel', ORIGENS_ORIENTAVEIS.includes(origem) && destino === 'pdf');
  };
  ajustarOrientacao(destinoSelecionado());

  document.querySelectorAll<HTMLInputElement>('input[name="destino"]').forEach((radio) => {
    radio.addEventListener('change', () => {
      ajustarOrientacao(radio.value);
      if (uid) void atualizarPreview(radio.value, origem, uid);
    });
  });
  document.querySelectorAll<HTMLInputElement>('input[name="_ori"]').forEach((radio) => {
    radio.addEventListener('change', () => {
      if (campoOrientacao) campoOrientacao.value = radio.value;
      if (destinoSelecionado() === 'pdf') void atualizarPreview('pdf', origem, uid);
    });
  });
}

function embutirPdf(viewer: HTMLElement, url: string, cabecalho = ''): void {
  viewer.innerHTML = `
    <div style="position:relative;width:100%;height:100%;display:flex;flex-direction:column;">
      ${cabecalho}
      <embed src="${url}#toolbar=0&navpanes=0&scrollbar=1" type="application/pdf" class="pdf-embed" style="flex:1;min-height:200px;">
    </div>`;
}

async function atualizarPreview(destino: string, origem: string, uid: string): Promise<void> {
  const viewer = porId('previewViewer');
  const sub = porId('previewSub');
  if (!viewer) return;
  const formato = destino.toUpperCase();
  const definirSub = (texto: string): void => {
    if (sub) sub.textContent = texto;
  };

  viewer.innerHTML = `<div class="preview-loading"><div class="spinner-preview"></div><span>${t('preview.generating', { format: formato })}</span></div>`;
  definirSub('...');

  // Sem caminho até PDF nesta máquina (nem o próprio destino), a referência visual não existe.
  const pdfPossivel = origem === 'pdf' || !!document.querySelector('input[name="destino"][value="pdf"]');

  try {
    if (destino === 'pdf') {
      const rotuloOri = orientacaoSelecionada() === 'paisagem' ? t('conv.ori.landscape') : t('conv.ori.portrait');
      embutirPdf(viewer, `/preview-convert/${uid}/pdf?orientacao=${orientacaoSelecionada()}`);
      definirSub(`PDF · ${rotuloOri}`);
    } else if (destino === 'png' || destino === 'jpg') {
      const url = `/preview-convert/${uid}/${destino}`;
      await new Promise<void>((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve();
        img.onerror = () => reject(new Error(t('preview.failed')));
        img.src = url;
      });
      viewer.innerHTML = `<img src="${url}" class="img-preview-visual" alt="${formato}">`;
      definirSub(t('preview.rendered', { format: formato }));
    } else if (destino === 'csv' || destino === 'xlsx') {
      const r = await fetch(`/preview-tabela/${uid}/${destino}`);
      if (!r.ok) throw new Error(await r.text());
      // HTML gerado pelo servidor com o conteúdo das células já escapado.
      viewer.innerHTML = `<div class="preview-scroll">${await r.text()}</div>`;
      definirSub(t('preview.full_data', { format: formato }));
    } else if ((destino === 'docx' || destino === 'pptx' || destino === 'ppt') && pdfPossivel) {
      const aviso = destino === 'docx' ? t('preview.docx_notice') : t('preview.ppt_notice', { format: formato });
      const detalhe = destino === 'docx' ? t('preview.docx_sub') : t('preview.ppt_sub');
      embutirPdf(viewer, `/preview-convert/${uid}/pdf`, `<div class="preview-aviso"><span>${aviso}</span><span class="preview-aviso-sub">${detalhe}</span></div>`);
      definirSub(t('preview.visual_ref', { format: formato }));
    } else {
      viewer.innerHTML = `<div class="preview-placeholder"><p class="placeholder-texto">${t('preview.not_available', { format: formato })}</p><p class="placeholder-sub">${t('preview.download_to_view')}</p></div>`;
      definirSub(formato);
    }
  } catch (e) {
    viewer.replaceChildren();
    const caixa = document.createElement('div');
    caixa.className = 'preview-erro-state';
    const titulo = document.createElement('span');
    titulo.textContent = t('preview.failed');
    const detalhe = document.createElement('span');
    detalhe.className = 'preview-erro-sub';
    detalhe.textContent = e instanceof Error ? e.message : '';
    caixa.append(titulo, detalhe);
    viewer.appendChild(caixa);
    definirSub('');
  }
}

function iniciarConversao(): void {
  const formulario = porId<HTMLFormElement>('converterForm');
  const botao = porId<HTMLButtonElement>('btnConverter');
  const area = porId('progressWrap');
  const barra = porId('progressBar');
  const rotulo = porId('progressLabel');
  if (!formulario || !botao) return;
  const textoOriginal = botao.innerHTML;

  formulario.addEventListener('submit', (e) => {
    e.preventDefault();
    if (botao.disabled) return;
    botao.disabled = true;
    botao.innerHTML = `<span>${t('job.processing')}</span><div class="spinner"></div>`;
    area?.classList.add('ativo');
    if (barra) {
      barra.style.width = '5%';
      barra.style.background = '';
    }
    const cancelamento = criarCancelamento(area);
    const restaurar = (): void => {
      cancelamento.remover();
      botao.disabled = false;
      botao.innerHTML = textoOriginal;
      area?.classList.remove('ativo');
      if (barra) barra.style.width = '0%';
    };

    executarFerramenta(formulario.action, new FormData(formulario), {
      atualizar(percent, texto) {
        if (barra) barra.style.width = `${Math.max(5, percent ?? 30)}%`;
        if (rotulo) rotulo.textContent = percent === null ? texto : `${texto} ${Math.round(percent)}%`;
      },
    }, cancelamento.sinal)
      .then((st) => {
        baixarResultado(st);
        mostrarToast(st.aviso ?? t('job.done'));
      })
      .catch((erro: unknown) => {
        if (erro instanceof Cancelado) mostrarToast(t('job.canceled'));
        else mostrarToast(erro instanceof Error ? erro.message : t('job.conn_err'), true);
      })
      .finally(restaurar);
  });
}
