import { aoCarregar } from './lib/dom';
import { aplicarTraducoes } from './lib/i18n';
import { iniciarShell } from './lib/shell';
import { iniciarTema } from './lib/theme';
import { iniciarAudio } from './pages/audio';
import { iniciarAvancadas } from './pages/avancadas';
import { iniciarConversor } from './pages/conversor';
import { iniciarHistorico } from './pages/historico';
import { iniciarVideo } from './pages/video';

const PAGINAS: Record<string, () => void> = {
  conversor: iniciarConversor,
  historico: iniciarHistorico,
  avancadas: iniciarAvancadas,
  audio: iniciarAudio,
  video: iniciarVideo,
};

aoCarregar(() => {
  iniciarTema();
  iniciarShell();
  PAGINAS[document.body.dataset.page ?? '']?.();
  aplicarTraducoes();
});
