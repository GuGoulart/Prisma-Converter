/** O que toda página tem: menu, sinal de vida para o servidor e atalhos declarativos do HTML. */
import { delegar, porId } from './dom';

const INTERVALO_SINAL_MS = 15_000;

function iniciarSinalDeVida(): void {
  // O servidor encerra sozinho quando a última janela fecha.
  const enviar = (): void => {
    fetch('/api/heartbeat', { method: 'POST', cache: 'no-store' }).catch(() => undefined);
  };
  enviar();
  setInterval(enviar, INTERVALO_SINAL_MS);
  window.addEventListener('focus', enviar);
}

function iniciarMenu(): void {
  const botao = porId('menuBtn');
  const menu = porId('sidebar');
  const fundo = porId('drawerOverlay');
  if (!botao || !menu) return;
  const ehMidia = ['audio', 'video'].includes(document.body.dataset.page ?? '');
  const definir = (aberto: boolean): void => {
    // As folhas de estilo usam nomes de classe diferentes.
    menu.classList.toggle('aberta', aberto);
    menu.classList.toggle('aberto', aberto);
    botao.classList.toggle('ativo', aberto);
    fundo?.classList.toggle('ativo', aberto);
    if (ehMidia && fundo) fundo.style.display = aberto ? 'block' : 'none';
    document.body.style.overflow = aberto ? 'hidden' : '';
  };
  botao.addEventListener('click', () => definir(!menu.classList.contains('aberta')));
  fundo?.addEventListener('click', () => definir(false));
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') definir(false);
  });
}

function iniciarAtalhos(): void {
  // data-click="id": repassa o clique para outro elemento (normalmente um input de arquivo).
  delegar('click', '[data-click]', (el, e) => {
    if (e.target instanceof HTMLInputElement) return;
    porId(el.dataset.click ?? '')?.click();
  });
  // data-chip="id" data-val="x": grupo de opções que grava em um input oculto.
  delegar('click', '[data-chip]', (el) => {
    el.closest('.opcoes-chips')?.querySelectorAll('.opcao-chip').forEach((c) => c.classList.remove('selecionado'));
    el.classList.add('selecionado');
    const campo = porId<HTMLInputElement>(el.dataset.chip ?? '');
    if (campo) campo.value = el.dataset.val ?? '';
    document.dispatchEvent(new CustomEvent('chipAlterado', { detail: { campo: el.dataset.chip } }));
  });
}

function iniciarEasterEgg(): void {
  document.querySelectorAll<HTMLElement>('.hud-reactor-core, .sidebar-logo .logo-mark, .mobile-logo').forEach((el) => {
    if (el.closest('a')) return;
    el.style.cursor = 'pointer';
    el.addEventListener('click', () => {
      let fundo = porId('dogEasterEggModal');
      if (!fundo) {
        fundo = document.createElement('div');
        fundo.id = 'dogEasterEggModal';
        fundo.className = 'dog-modal-overlay';
        fundo.innerHTML = `
          <div class="dog-modal-card">
            <button class="dog-modal-close">&times;</button>
            <img src="/static/dog_easter_egg.png" alt="Cachorro de Chapéu" class="dog-modal-img">
            <div class="dog-modal-text">socorro</div>
          </div>`;
        document.body.appendChild(fundo);
        const modal = fundo;
        modal.addEventListener('click', (ev) => {
          if (ev.target === modal || (ev.target instanceof Element && ev.target.closest('.dog-modal-close'))) modal.classList.remove('ativo');
        });
      }
      fundo.classList.add('ativo');
    });
  });
}

/** Instalações antigas registravam um service worker que pode continuar ativo. */
function removerServiceWorkerAntigo(): void {
  if ('serviceWorker' in navigator) {
    void navigator.serviceWorker.getRegistrations().then((rs) => rs.forEach((r) => void r.unregister()));
  }
}

export function iniciarShell(): void {
  iniciarSinalDeVida();
  iniciarMenu();
  iniciarAtalhos();
  iniciarEasterEgg();
  removerServiceWorkerAntigo();
}
