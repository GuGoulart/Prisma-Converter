/** Temas e aplicação das cores: também roda em boot.ts, antes da primeira pintura. */
export type Modo = 'dark' | 'light';

export interface Preset {
  namePt: string;
  nameEn: string;
  nameEs: string;
  color: string;
  hover: string;
  text: string;
  glow: string;
}

export const PRESETS: Record<Modo, Record<string, Preset>> = {
  dark: {
    red: { namePt: 'Vermelho Prisma', nameEn: 'Prisma Red', nameEs: 'Rojo Prisma', color: '#ff3b3b', hover: '#ff5252', text: '#ffffff', glow: 'rgba(255, 59, 59, 0.35)' },
    emerald: { namePt: 'Verde Prisma', nameEn: 'Prisma Green', nameEs: 'Verde Prisma', color: '#c8ff00', hover: '#d4ff1a', text: '#0a0a0a', glow: 'rgba(200, 255, 0, 0.35)' },
    cyan: { namePt: 'Ciano Elétrico', nameEn: 'Electric Cyan', nameEs: 'Cian Eléctrico', color: '#00f0ff', hover: '#33f3ff', text: '#0a0a0a', glow: 'rgba(0, 240, 255, 0.35)' },
    purple: { namePt: 'Roxo Neon', nameEn: 'Neon Purple', nameEs: 'Púrpura Neón', color: '#a855f7', hover: '#b666ff', text: '#ffffff', glow: 'rgba(168, 85, 247, 0.35)' },
    orange: { namePt: 'Laranja Vibrante', nameEn: 'Vibrant Orange', nameEs: 'Naranja Vibrante', color: '#ff7700', hover: '#ff8c26', text: '#ffffff', glow: 'rgba(255, 119, 0, 0.35)' },
    pink: { namePt: 'Rosa Magenta', nameEn: 'Magenta Pink', nameEs: 'Rosa Magenta', color: '#ff007f', hover: '#ff3399', text: '#ffffff', glow: 'rgba(255, 0, 127, 0.35)' },
    blue: { namePt: 'Azul Elétrico', nameEn: 'Electric Blue', nameEs: 'Azul Eléctrico', color: '#3b82f6', hover: '#60a5fa', text: '#ffffff', glow: 'rgba(59, 130, 246, 0.35)' },
    indigo: { namePt: 'Índigo Neon', nameEn: 'Neon Indigo', nameEs: 'Índigo Neón', color: '#6366f1', hover: '#818cf8', text: '#ffffff', glow: 'rgba(99, 102, 241, 0.35)' },
    mint: { namePt: 'Verde Menta', nameEn: 'Mint Green', nameEs: 'Verde Menta', color: '#10b981', hover: '#34d399', text: '#0a0a0a', glow: 'rgba(16, 185, 129, 0.35)' },
    amber: { namePt: 'Âmbar Dourado', nameEn: 'Golden Amber', nameEs: 'Ámbar Dorado', color: '#ffb703', hover: '#ffc333', text: '#0a0a0a', glow: 'rgba(255, 183, 3, 0.35)' },
  },
  light: {
    red: { namePt: 'Vermelho Prisma', nameEn: 'Prisma Red', nameEs: 'Rojo Prisma', color: '#dc2626', hover: '#b91c1c', text: '#ffffff', glow: 'rgba(220, 38, 38, 0.35)' },
    emerald: { namePt: 'Verde Esmeralda', nameEn: 'Emerald Green', nameEs: 'Verde Esmeralda', color: '#059669', hover: '#047857', text: '#ffffff', glow: 'rgba(5, 150, 105, 0.35)' },
    cyan: { namePt: 'Ciano Profundo', nameEn: 'Deep Cyan', nameEs: 'Cian Profundo', color: '#0891b2', hover: '#0e7490', text: '#ffffff', glow: 'rgba(8, 145, 178, 0.35)' },
    purple: { namePt: 'Violeta Imperial', nameEn: 'Imperial Purple', nameEs: 'Violeta Imperial', color: '#7c3aed', hover: '#6d28d9', text: '#ffffff', glow: 'rgba(124, 58, 237, 0.35)' },
    orange: { namePt: 'Laranja Âmbar', nameEn: 'Amber Orange', nameEs: 'Naranja Ámbar', color: '#ea580c', hover: '#c2410c', text: '#ffffff', glow: 'rgba(234, 88, 12, 0.35)' },
    pink: { namePt: 'Rosa Carmim', nameEn: 'Carmine Rose', nameEs: 'Rosa Carmín', color: '#db2777', hover: '#be185d', text: '#ffffff', glow: 'rgba(219, 39, 119, 0.35)' },
    blue: { namePt: 'Azul Real', nameEn: 'Royal Blue', nameEs: 'Azul Real', color: '#2563eb', hover: '#1d4ed8', text: '#ffffff', glow: 'rgba(37, 99, 235, 0.35)' },
    indigo: { namePt: 'Índigo Elegante', nameEn: 'Elegant Indigo', nameEs: 'Índigo Elegante', color: '#4f46e5', hover: '#4338ca', text: '#ffffff', glow: 'rgba(79, 70, 229, 0.35)' },
    mint: { namePt: 'Verde Menta', nameEn: 'Mint Green', nameEs: 'Verde Menta', color: '#0d9488', hover: '#0f766e', text: '#ffffff', glow: 'rgba(13, 148, 136, 0.35)' },
    amber: { namePt: 'Âmbar Dourado', nameEn: 'Golden Amber', nameEs: 'Ámbar Dorado', color: '#d97706', hover: '#b45309', text: '#ffffff', glow: 'rgba(217, 119, 6, 0.35)' },
  },
};

const PADRAO: Record<Modo, string> = { dark: 'red', light: 'purple' };

export function modoSalvo(): Modo {
  return localStorage.getItem('theme') === 'light' ? 'light' : 'dark';
}

export function corSalva(modo: Modo): string {
  const salva = localStorage.getItem(modo === 'light' ? 'theme_accent_light' : 'theme_accent_dark');
  return salva && PRESETS[modo][salva] ? salva : PADRAO[modo];
}

export function aplicarTema(modo: Modo, chave: string): void {
  const raiz = document.documentElement;
  if (modo === 'light') raiz.setAttribute('data-theme', 'light');
  else raiz.removeAttribute('data-theme');
  const preset = PRESETS[modo][chave] ?? PRESETS[modo][PADRAO[modo]];
  if (!preset) return;
  raiz.style.setProperty('--accent', preset.color);
  raiz.style.setProperty('--accent-hover', preset.hover);
  raiz.style.setProperty('--accent-text', preset.text);
  raiz.style.setProperty('--accent-glow', preset.glow);
  localStorage.setItem('theme', modo);
  localStorage.setItem(modo === 'light' ? 'theme_accent_light' : 'theme_accent_dark', chave);
}
