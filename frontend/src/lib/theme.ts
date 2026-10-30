/** Modal de personalização: idioma, modo e cor de destaque. */
import { aplicarTraducoes, definirIdioma, idiomaAtual } from './i18n';
import { MODAL_HTML } from './theme_modal';
import { aplicarTema, corSalva, modoSalvo, PRESETS, type Modo } from './theme_presets';

function renderizarCores(modo: Modo, ativa: string): void {
  const container = document.getElementById('themeSwatchesContainer');
  if (!container) return;
  const idioma = idiomaAtual();
  container.replaceChildren();
  for (const [chave, item] of Object.entries(PRESETS[modo])) {
    const nome = idioma === 'en' ? item.nameEn : idioma === 'es' ? item.nameEs : item.namePt;
    const botao = document.createElement('button');
    botao.type = 'button';
    botao.className = `theme-swatch-btn ${chave === ativa ? 'active' : ''}`;
    botao.title = nome;
    botao.style.setProperty('--swatch-color', item.color);
    botao.style.setProperty('--swatch-glow', item.glow);
    botao.innerHTML = `
      <div class="swatch-box-wrap"><span class="swatch-box" style="background-color: ${item.color};"></span></div>
      <span class="swatch-name">${nome}</span>
      <span class="swatch-check">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
      </span>`;
    botao.addEventListener('click', () => {
      aplicarTema(modo, chave);
      atualizarModal();
    });
    container.appendChild(botao);
  }
}

function atualizarModal(): void {
  const modo = modoSalvo();
  document.querySelectorAll<HTMLElement>('.theme-mode-square-btn').forEach((b) => {
    b.classList.toggle('active', b.dataset.mode === modo);
  });
  document.getElementById('themeAccentSub')?.setAttribute('data-i18n', modo === 'light' ? 'customizer.accent.lightSub' : 'customizer.accent.darkSub');
  aplicarTraducoes();
  renderizarCores(modo, corSalva(modo));
}

function abrir(): void {
  const modal = document.getElementById('themeCustomizerModal');
  if (!modal) return;
  atualizarModal();
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
}

function fechar(): void {
  const modal = document.getElementById('themeCustomizerModal');
  if (!modal) return;
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
}

export function iniciarTema(): void {
  document.body.insertAdjacentHTML('beforeend', MODAL_HTML);
  document.getElementById('themeToggle')?.addEventListener('click', (e) => {
    e.preventDefault();
    abrir();
  });
  document.addEventListener('click', (e) => {
    const alvo = e.target;
    if (!(alvo instanceof Element)) return;
    if (alvo.closest('#closeCustomizerBtn, #doneCustomizerBtn') || alvo.classList.contains('theme-modal-overlay')) fechar();
    const botaoModo = alvo.closest<HTMLElement>('.theme-mode-square-btn');
    if (botaoModo) {
      const modo: Modo = botaoModo.dataset.mode === 'light' ? 'light' : 'dark';
      aplicarTema(modo, corSalva(modo));
      atualizarModal();
    }
    const botaoIdioma = alvo.closest<HTMLElement>('.btn-lang-opt');
    if (botaoIdioma?.dataset.lang) definirIdioma(botaoIdioma.dataset.lang);
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') fechar();
  });
  window.addEventListener('languageChanged', atualizarModal);
}
