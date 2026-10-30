import { postJson } from '../lib/api';
import { baixar, delegar, porId } from '../lib/dom';
import { t } from '../lib/i18n';
import { mostrarToast } from '../lib/toast';

const TEMPORIZADAS = ['5min', '15min'];

function formatarRestante(segundos: number): string {
  return `${String(Math.floor(segundos / 60)).padStart(2, '0')}:${String(segundos % 60).padStart(2, '0')}`;
}

function atualizarBotaoLote(): void {
  const botao = porId<HTMLButtonElement>('downloadAllHistory');
  if (!botao) return;
  const itens = Array.from(document.querySelectorAll<HTMLElement>('.historico-item'));
  const temAtivo = itens.some((i) => i.dataset.apagado !== 'true' && TEMPORIZADAS.includes(i.dataset.policy ?? ''));
  botao.disabled = !temAtivo;
  botao.classList.toggle('btn-disabled', !temAtivo);
}

function marcarApagado(item: HTMLElement): void {
  item.dataset.apagado = 'true';
  const superior = item.querySelector('.hist-card-top-left');
  superior?.querySelectorAll('.hist-timer, .btn-retention-restore').forEach((el) => el.remove());
  const direita = item.querySelector('.historico-item-right');
  if (direita) {
    direita.replaceChildren();
    const selo = document.createElement('span');
    selo.className = 'hist-apagado-badge';
    selo.textContent = t('conv.history.deleted');
    direita.appendChild(selo);
  }
  atualizarBotaoLote();
}

function atualizarContadores(): void {
  const agora = Math.floor(Date.now() / 1000);
  document.querySelectorAll<HTMLElement>('.historico-item').forEach((item) => {
    if (item.dataset.apagado === 'true' || !item.dataset.expires) return;
    const restante = Number.parseInt(item.dataset.expires, 10) - agora;
    if (restante <= 0) marcarApagado(item);
    else {
      const valor = item.querySelector('.hist-timer-val');
      if (valor) valor.textContent = formatarRestante(restante);
    }
  });
}

export function iniciarHistorico(): void {
  atualizarContadores();
  setInterval(atualizarContadores, 1000);
  atualizarBotaoLote();

  delegar('click', '[data-action="renovar"]', (botao) => {
    const id = botao.dataset.job ?? '';
    void postJson<{ expira_em?: number }>(`/api/historico/renovar/${id}`).then((r) => {
      if (r.erro || !r.expira_em) {
        mostrarToast(r.erro ?? t('history.renew_err'), true);
        return;
      }
      const item = botao.closest<HTMLElement>('.historico-item');
      if (item) item.dataset.expires = String(r.expira_em);
      atualizarContadores();
      mostrarToast(t('history.renewed'));
    });
  });

  porId('downloadAllHistory')?.addEventListener('click', () => {
    baixar('/api/historico/zip-todos', 'prisma_lote_arquivos.zip');
    mostrarToast(t('history.zip_ready'));
  });

  const modal = porId('destroyHistoryModal');
  const fechar = (): void => {
    modal?.classList.remove('open');
    modal?.setAttribute('aria-hidden', 'true');
  };
  porId('destroyAllHistory')?.addEventListener('click', () => {
    modal?.classList.add('open');
    modal?.setAttribute('aria-hidden', 'false');
  });
  porId('closeDestroyModal')?.addEventListener('click', fechar);
  porId('cancelDestroyHistory')?.addEventListener('click', fechar);
  modal?.addEventListener('click', (e) => {
    if (e.target === modal) fechar();
  });
  porId('confirmDestroyHistory')?.addEventListener('click', () => {
    void postJson<{ mensagem?: string }>('/api/historico/destruir-tudo').then((r) => {
      fechar();
      if (r.erro) {
        mostrarToast(r.erro, true);
        return;
      }
      document.querySelectorAll<HTMLElement>('.historico-item').forEach(marcarApagado);
      mostrarToast(r.mensagem ?? '');
    });
  });

  const retencao = porId('historyRetention');
  retencao?.addEventListener('click', (e) => {
    const botao = e.target instanceof Element ? e.target.closest<HTMLElement>('.btn-ret-opt') : null;
    if (!botao) return;
    void postJson('/api/historico/set-politica', { politica: botao.dataset.policy }).then((r) => {
      if (r.erro) {
        mostrarToast(r.erro, true);
        return;
      }
      retencao.querySelectorAll<HTMLElement>('.btn-ret-opt').forEach((b) => b.classList.toggle('active', b === botao));
      mostrarToast(t('history.retention_saved'));
    });
  });
}
