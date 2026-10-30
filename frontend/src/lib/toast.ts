let temporizador: number | undefined;

export function mostrarToast(mensagem: string, erro = false): void {
  const toast = document.getElementById('toast');
  const texto = toast?.querySelector('.toast-msg');
  if (!toast || !texto) return;
  texto.textContent = mensagem;
  texto.removeAttribute('data-i18n');
  const icone = toast.querySelector('.toast-icone');
  if (icone) icone.textContent = erro ? '✕' : '✓';
  toast.classList.toggle('erro', erro);
  toast.classList.add('visivel');
  window.clearTimeout(temporizador);
  temporizador = window.setTimeout(() => toast.classList.remove('visivel'), 4000);
}
