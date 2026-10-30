/** Atalhos para o DOM. */

export function porId<T extends HTMLElement = HTMLElement>(id: string): T | null {
  return document.getElementById(id) as T | null;
}

export function valor(id: string, padrao = ''): string {
  return porId<HTMLInputElement | HTMLSelectElement>(id)?.value || padrao;
}

export function aoCarregar(fn: () => void): void {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
  else fn();
}

export function formatarTamanho(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1_048_576) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1_073_741_824) return `${(bytes / 1_048_576).toFixed(1)} MB`;
  return `${(bytes / 1_073_741_824).toFixed(1)} GB`;
}

export function baixar(url: string, nome?: string): void {
  const link = document.createElement('a');
  link.href = url;
  if (nome) link.download = nome;
  document.body.appendChild(link);
  link.click();
  link.remove();
}

/** Delegação de eventos: um único ouvinte por tipo, para elementos inclusive criados depois. */
export function delegar<K extends keyof HTMLElementEventMap>(
  tipo: K,
  seletor: string,
  fn: (alvo: HTMLElement, evento: HTMLElementEventMap[K]) => void,
): void {
  document.addEventListener(tipo, (evento) => {
    const origem = evento.target;
    if (!(origem instanceof Element)) return;
    const alvo = origem.closest<HTMLElement>(seletor);
    if (alvo) fn(alvo, evento as HTMLElementEventMap[K]);
  });
}
