/** Comunicação com o backend. Toda ferramenta segue: envia → acompanha o job → resultado. */
import { baixar } from './dom';
import { t } from './i18n';

export interface StatusJob {
  job_id: string;
  status: 'fila' | 'executando' | 'concluido' | 'erro' | 'cancelado';
  percent: number;
  concluido: boolean;
  erro: string | null;
  aviso: string | null;
  dados: Record<string, unknown> | null;
  nome_download: string;
  tamanho: string | null;
  download_url: string | null;
}

export interface Progresso {
  /** percent === null significa "em andamento, sem porcentagem conhecida". */
  atualizar(percent: number | null, texto: string): void;
}

export class Cancelado extends Error {}

export function tokenCsrf(): string {
  return document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.content ?? '';
}

export function postJson<T = Record<string, unknown>>(url: string, corpo?: unknown): Promise<T & { erro?: string }> {
  return fetch(url, {
    method: 'POST',
    headers: { 'X-CSRFToken': tokenCsrf(), 'Content-Type': 'application/json' },
    body: corpo === undefined ? undefined : JSON.stringify(corpo),
  }).then(async (r) => {
    const dados = (await r.json().catch(() => ({}))) as T & { erro?: string };
    if (!r.ok && !dados.erro) dados.erro = t('job.conn_err');
    return dados;
  });
}

function esperar(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Usa XHR porque fetch não informa o progresso de upload, importante em arquivos grandes. */
function enviar(url: string, dados: FormData, progresso: Progresso, sinal: AbortSignal): Promise<string> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url);
    xhr.setRequestHeader('X-CSRFToken', tokenCsrf());
    xhr.responseType = 'json';
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) progresso.atualizar(Math.round((e.loaded / e.total) * 100), t('job.sending'));
    };
    xhr.onload = () => {
      const corpo = xhr.response as { job_id?: string; erro?: string } | null;
      if (xhr.status === 202 && corpo?.job_id) resolve(corpo.job_id);
      else reject(new Error(corpo?.erro ?? t('job.conn_err')));
    };
    xhr.onerror = () => reject(new Error(t('job.conn_err')));
    xhr.onabort = () => reject(new Cancelado());
    sinal.addEventListener('abort', () => xhr.abort());
    xhr.send(dados);
  });
}

async function acompanhar(id: string, progresso: Progresso, sinal: AbortSignal): Promise<StatusJob> {
  let falhas = 0;
  let cancelou = false;
  for (;;) {
    if (sinal.aborted && !cancelou) {
      cancelou = true;
      await postJson(`/api/jobs/${id}/cancelar`).catch(() => undefined);
    }
    try {
      const r = await fetch(`/api/jobs/${id}`, { cache: 'no-store' });
      if (r.status === 404) throw new Error(t('job.conn_err'));
      const st = (await r.json()) as StatusJob;
      falhas = 0;
      if (st.concluido) return st;
      if (st.status === 'fila') progresso.atualizar(null, t('job.queued'));
      else progresso.atualizar(st.percent > 0 ? st.percent : null, t('job.processing'));
    } catch (e) {
      if (++falhas > 20) throw e instanceof Error ? e : new Error(t('job.conn_err'));
    }
    await esperar(400);
  }
}

/** Executa uma ferramenta de ponta a ponta e devolve o job concluído. Lança Error com mensagem pronta. */
export async function executarFerramenta(
  url: string,
  dados: FormData,
  progresso: Progresso,
  sinal: AbortSignal,
): Promise<StatusJob> {
  const id = await enviar(url, dados, progresso, sinal);
  const st = await acompanhar(id, progresso, sinal);
  if (st.status === 'cancelado') throw new Cancelado();
  if (st.status === 'erro') throw new Error(st.erro ?? t('job.conn_err'));
  return st;
}

export function baixarResultado(st: StatusJob): void {
  if (st.download_url) baixar(st.download_url, st.nome_download);
}

/** Botão "Cancelar" exibido enquanto a ferramenta roda. */
export function criarCancelamento(depoisDe: Element | null): { sinal: AbortSignal; remover(): void } {
  const controle = new AbortController();
  const botao = document.createElement('button');
  botao.type = 'button';
  botao.className = 'btn-job-cancel';
  botao.textContent = t('job.cancel');
  botao.addEventListener('click', () => {
    botao.disabled = true;
    controle.abort();
  });
  depoisDe?.insertAdjacentElement('afterend', botao);
  return { sinal: controle.signal, remover: () => botao.remove() };
}
