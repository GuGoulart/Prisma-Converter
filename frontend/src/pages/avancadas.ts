import { baixarResultado, Cancelado, criarCancelamento, executarFerramenta, type StatusJob } from '../lib/api';
import { porId } from '../lib/dom';
import { t } from '../lib/i18n';
import { mostrarToast } from '../lib/toast';
import { iniciarAnimacaoTopo } from './avancadas_topo';

/** Roda a ferramenta deixando o botão do formulário como indicador de progresso. */
function executarDoFormulario(formulario: HTMLFormElement, url: string, aoConcluir: (st: StatusJob) => void): void {
  const botao = formulario.querySelector<HTMLButtonElement>('button[type="submit"]');
  if (!botao || botao.disabled) return;
  const original = botao.innerHTML;
  formulario.querySelector('.ferramenta-erro')?.remove();
  botao.disabled = true;
  const cancelamento = criarCancelamento(botao);

  executarFerramenta(url, new FormData(formulario), {
    atualizar(percent, texto) {
      botao.innerHTML = `<span>${percent === null ? texto : `${texto} ${Math.round(percent)}%`}</span><div class="spinner"></div>`;
    },
  }, cancelamento.sinal)
    .then(aoConcluir)
    .catch((erro: unknown) => {
      if (erro instanceof Cancelado) {
        mostrarToast(t('job.canceled'));
        return;
      }
      const aviso = document.createElement('p');
      aviso.className = 'ferramenta-erro';
      aviso.textContent = erro instanceof Error ? erro.message : t('job.conn_err');
      botao.insertAdjacentElement('beforebegin', aviso);
    })
    .finally(() => {
      cancelamento.remover();
      botao.disabled = false;
      botao.innerHTML = original;
    });
}

function iniciarFormularios(): void {
  document.querySelectorAll<HTMLFormElement>('form[action^="/api/"]').forEach((formulario) => {
    formulario.addEventListener('submit', (e) => {
      e.preventDefault();
      executarDoFormulario(formulario, formulario.getAttribute('action') ?? '', (st) => {
        baixarResultado(st);
        mostrarToast(st.aviso ?? t('job.done'));
      });
    });
  });
}

function iniciarNomesDeArquivo(): void {
  const pares: Array<[string, string]> = [
    ['splitInput', 'splitFileName'], ['protectInput', 'protectFileName'], ['unprotectInput', 'unprotectFileName'],
    ['compressInput', 'compressFileName'], ['watermarkInput', 'watermarkFileName'], ['extractInput', 'extractFileName'],
    ['manipulateInput', 'manipulateFileName'], ['qrLerInput', 'qrLerFileName'], ['paletaInput', 'paletaFileName'],
    ['criptoInput', 'criptoFileName'], ['decriptoInput', 'decriptoFileName'], ['hashInput', 'hashFileName'],
  ];
  for (const [entradaId, nomeId] of pares) {
    const entrada = porId<HTMLInputElement>(entradaId);
    const nome = porId(nomeId);
    if (!entrada || !nome) continue;
    const atualizar = (): void => {
      const arquivo = entrada.files?.[0];
      nome.removeAttribute('data-i18n');
      nome.textContent = arquivo ? arquivo.name : t('file.none');
      nome.style.color = arquivo ? 'var(--text)' : 'var(--muted)';
    };
    entrada.addEventListener('change', atualizar);
    const cartao = entrada.closest<HTMLElement>('.pdf-tool-card');
    if (!cartao) continue;
    for (const tipo of ['dragover', 'dragenter'] as const) {
      cartao.addEventListener(tipo, (e) => {
        e.preventDefault();
        cartao.style.borderColor = 'var(--accent)';
      });
    }
    cartao.addEventListener('dragleave', () => {
      cartao.style.borderColor = '';
    });
    cartao.addEventListener('drop', (e) => {
      e.preventDefault();
      cartao.style.borderColor = '';
      if (e.dataTransfer?.files.length) {
        entrada.files = e.dataTransfer.files;
        atualizar();
      }
    });
  }
}

function iniciarAcumuladores(): void {
  const grupos: Array<[string, string, string, string]> = [
    ['mergeInput', 'mergeListContainer', 'mergeEmptyMsg', 'P'],
    ['mergeDataInput', 'mergeDataListContainer', 'mergeDataEmptyMsg', 'D'],
    ['comprimirInput', 'comprimirListContainer', 'comprimirEmptyMsg', '•'],
    ['zipSenhaInput', 'zipSenhaListContainer', 'zipSenhaEmptyMsg', '•'],
    ['renomearInput', 'renomearListContainer', 'renomearEmptyMsg', '•'],
  ];
  for (const [entradaId, listaId, vazioId, prefixo] of grupos) {
    const entrada = porId<HTMLInputElement>(entradaId);
    const lista = porId(listaId);
    const vazio = porId(vazioId);
    if (!entrada || !lista) continue;
    // Selecionar de novo acrescenta à lista em vez de substituí-la.
    const acumulado = new DataTransfer();
    entrada.addEventListener('change', () => {
      for (const arquivo of Array.from(entrada.files ?? [])) acumulado.items.add(arquivo);
      entrada.files = acumulado.files;
      lista.querySelectorAll('.merge-item').forEach((i) => i.remove());
      if (vazio && acumulado.files.length) vazio.style.display = 'none';
      for (const arquivo of Array.from(acumulado.files)) {
        const item = document.createElement('div');
        item.className = 'merge-item';
        item.textContent = `${prefixo} ${arquivo.name}`;
        item.style.cssText = 'font-size:12px;color:var(--text);background:var(--surface);padding:4px 8px;border-radius:4px;';
        lista.appendChild(item);
      }
    });
  }
}

function iniciarDivisao(): void {
  const modo = porId<HTMLSelectElement>('splitModo');
  const parametro = porId<HTMLInputElement>('splitParametro');
  const info = porId('splitInfo');
  if (!modo || !parametro || !info) return;
  const atualizar = (): void => {
    const individual = modo.value === 'individual';
    parametro.style.display = individual ? 'none' : 'block';
    parametro.required = !individual;
    if (modo.value === 'fixo') parametro.placeholder = t('split.ph.fix');
    if (modo.value === 'custom') parametro.placeholder = t('split.ph.cust');
    info.textContent = modo.value === 'fixo' ? t('split.info.fix') : modo.value === 'custom' ? t('split.info.cust') : t('split.info.ind');
  };
  modo.addEventListener('change', atualizar);
  window.addEventListener('languageChanged', atualizar);
}

function copiavel(el: HTMLElement, texto: string): void {
  el.title = t('hash.copied');
  el.addEventListener('click', () => {
    void navigator.clipboard.writeText(texto).then(() => mostrarToast(t('hash.copied')));
  });
}

function iniciarLeitorQr(): void {
  const formulario = porId<HTMLFormElement>('qrLerForm');
  const resultado = porId('qrLerResultado');
  if (!formulario || !resultado) return;
  formulario.addEventListener('submit', (e) => {
    e.preventDefault();
    executarDoFormulario(formulario, '/api/qr/ler', (st) => {
      resultado.replaceChildren();
      // O conteúdo de um QR Code é externo e não confiável: entra sempre como texto.
      for (const codigo of (st.dados?.codigos ?? []) as Array<{ tipo: string; dados: string }>) {
        const linha = document.createElement('div');
        linha.className = 'qr-item';
        const tipo = document.createElement('span');
        tipo.className = 'qr-tipo';
        tipo.textContent = `[${codigo.tipo}]`;
        const dados = document.createElement('span');
        dados.className = 'qr-dados';
        dados.textContent = codigo.dados;
        copiavel(dados, codigo.dados);
        linha.append(tipo, dados);
        resultado.appendChild(linha);
      }
      resultado.style.display = 'block';
    });
  });
}

function iniciarPaleta(): void {
  const formulario = porId<HTMLFormElement>('paletaForm');
  const resultado = porId('paletaResultado');
  if (!formulario || !resultado) return;
  formulario.addEventListener('submit', (e) => {
    e.preventDefault();
    executarDoFormulario(formulario, '/api/img/paleta', (st) => {
      resultado.replaceChildren();
      const grade = document.createElement('div');
      grade.className = 'paleta-swatches';
      for (const cor of (st.dados?.paleta ?? []) as Array<{ hex: string; percentual: number }>) {
        const amostra = document.createElement('div');
        amostra.className = 'paleta-swatch';
        amostra.style.background = cor.hex;
        amostra.title = `${cor.hex} — ${cor.percentual}%`;
        const rotulo = document.createElement('span');
        rotulo.className = 'paleta-swatch-label';
        rotulo.textContent = cor.hex;
        amostra.appendChild(rotulo);
        amostra.addEventListener('click', () => {
          void navigator.clipboard.writeText(cor.hex).then(() => mostrarToast(t('palette.copied', { hex: cor.hex })));
        });
        grade.appendChild(amostra);
      }
      resultado.appendChild(grade);
      resultado.style.display = 'block';
    });
  });
}

function iniciarHash(): void {
  const formulario = porId<HTMLFormElement>('hashForm');
  const resultado = porId('hashResultado');
  if (!formulario || !resultado) return;
  formulario.addEventListener('submit', (e) => {
    e.preventDefault();
    executarDoFormulario(formulario, '/api/file/hash', (st) => {
      const d = (st.dados ?? {}) as Record<string, string>;
      resultado.replaceChildren();
      const titulo = document.createElement('div');
      titulo.style.cssText = 'margin-bottom:8px;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:1px';
      titulo.textContent = `${d.nome ?? ''} — ${d.tamanho_formatado ?? ''}`;
      resultado.appendChild(titulo);
      for (const [rotulo, chave] of [['MD5', 'md5'], ['SHA-1', 'sha1'], ['SHA-256', 'sha256']] as const) {
        const linha = document.createElement('div');
        const nome = document.createElement('span');
        nome.className = 'hash-label';
        nome.textContent = `${rotulo}: `;
        const valor = document.createElement('span');
        valor.className = 'hash-value';
        valor.textContent = d[chave] ?? '';
        copiavel(valor, d[chave] ?? '');
        linha.append(nome, valor);
        resultado.appendChild(linha);
      }
      resultado.style.display = 'block';
    });
  });
}

export function iniciarAvancadas(): void {
  iniciarFormularios();
  iniciarNomesDeArquivo();
  iniciarAcumuladores();
  iniciarDivisao();
  iniciarLeitorQr();
  iniciarPaleta();
  iniciarHash();
  iniciarAnimacaoTopo();
}
