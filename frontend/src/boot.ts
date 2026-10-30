// Carregado de forma bloqueante no <head>: aplica o tema antes da primeira pintura.
import { aplicarTema, corSalva, modoSalvo } from './lib/theme_presets';

const modo = modoSalvo();
aplicarTema(modo, corSalva(modo));
