import { en } from '../i18n/en';
import { es } from '../i18n/es';
import { pt, type Chave } from '../i18n/pt';

export type Idioma = 'pt' | 'en' | 'es';
const DICIONARIOS: Record<Idioma, Partial<Record<Chave, string>>> = { pt, en, es };

export function idiomaAtual(): Idioma {
  const salvo = localStorage.getItem('prisma_lang');
  if (salvo === 'pt' || salvo === 'en' || salvo === 'es') return salvo;
  const navegador = navigator.language.slice(0, 2).toLowerCase();
  return navegador === 'en' || navegador === 'es' ? navegador : 'pt';
}

export function t(chave: Chave, substituicoes: Record<string, string> = {}): string {
  let texto: string = DICIONARIOS[idiomaAtual()][chave] ?? pt[chave];
  for (const [nome, valor] of Object.entries(substituicoes)) texto = texto.replace(`{${nome}}`, valor);
  return texto;
}

function ehChave(valor: string): valor is Chave {
  return valor in pt;
}

export function aplicarTraducoes(): void {
  const idioma = idiomaAtual();
  document.documentElement.lang = idioma === 'pt' ? 'pt-BR' : idioma;
  // Os textos vêm só dos dicionários do próprio app, e alguns têm marcação (<em>, <br>).
  document.querySelectorAll<HTMLElement>('[data-i18n]').forEach((el) => {
    const chave = el.dataset.i18n ?? '';
    if (ehChave(chave)) el.innerHTML = t(chave);
  });
  document.querySelectorAll<HTMLInputElement>('[data-i18n-ph]').forEach((el) => {
    const chave = el.dataset.i18nPh ?? '';
    if (ehChave(chave)) el.placeholder = t(chave);
  });
  document.querySelectorAll<HTMLElement>('[data-i18n-title]').forEach((el) => {
    const chave = el.dataset.i18nTitle ?? '';
    if (ehChave(chave)) el.title = t(chave);
  });
  document.querySelectorAll<HTMLElement>('.btn-lang-opt').forEach((btn) => {
    btn.classList.toggle('ativo', btn.dataset.lang === idioma);
  });
}

export function definirIdioma(idioma: string): void {
  if (idioma !== 'pt' && idioma !== 'en' && idioma !== 'es') return;
  localStorage.setItem('prisma_lang', idioma);
  aplicarTraducoes();
  window.dispatchEvent(new CustomEvent('languageChanged', { detail: { idioma } }));
}
