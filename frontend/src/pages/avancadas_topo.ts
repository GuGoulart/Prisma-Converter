/** Decoração da barra superior das Ferramentas Avançadas. */
const ICONES = [
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>',
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="3"></circle><circle cx="6" cy="18" r="3"></circle><line x1="20" y1="4" x2="8.12" y2="15.88"></line><line x1="14.47" y1="14.48" x2="20" y2="20"></line><line x1="8.12" y1="8.12" x2="12" y2="12"></line></svg>',
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>',
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'
        ];

const NOS: Array<{ type: string; svg: string }> = [
            { type: 'node-encrypt', svg: '<svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>' },
            { type: 'node-compress', svg: '<svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>' },
            { type: 'node-hash', svg: '<svg viewBox="0 0 24 24"><line x1="4" y1="9" x2="20" y2="9"></line><line x1="4" y1="15" x2="20" y2="15"></line><line x1="10" y1="3" x2="8" y2="21"></line><line x1="16" y1="3" x2="14" y2="21"></line></svg>' },
            { type: 'node-encrypt', svg: '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>' },
            { type: 'node-compress', svg: '<svg viewBox="0 0 24 24"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>' },
            { type: 'node-hash', svg: '<svg viewBox="0 0 24 24"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>' },
            { type: 'node-encrypt', svg: '<svg viewBox="0 0 24 24"><path d="M21 2l-2 2m-3 3l-6.5 6.5a4.5 4.5 0 1 1-2-2L14 5l3-3 4 4z"></path></svg>' },
            { type: 'node-compress', svg: '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>' },
            { type: 'node-hash', svg: '<svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line></svg>' },
            { type: 'node-compress', svg: '<svg viewBox="0 0 24 24"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>' },
            { type: 'node-encrypt', svg: '<svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"></rect><path d="M7 11V7a5 5 0 0 1 9.9-1"></path></svg>' },
            { type: 'node-hash', svg: '<svg viewBox="0 0 24 24"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>' },
            { type: 'node-compress', svg: '<svg viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>' },
            { type: 'node-hash', svg: '<svg viewBox="0 0 24 24"><path d="M8 3H5a2 2 0 0 0-2 2v3m0 8v3a2 2 0 0 0 2 2h3m8-18h3a2 2 0 0 1 2 2v3m0 8v3a2 2 0 0 1-2 2h-3"></path></svg>' }
        ];

function gerarIcone(container: HTMLElement): void {
  if (document.hidden) return;
  const el = document.createElement('div');
  el.className = 'storm-icon';
  el.innerHTML = ICONES[Math.floor(Math.random() * ICONES.length)] ?? '';
  const tamanho = 14 + Math.random() * 14;
  el.style.width = el.style.height = `${tamanho}px`;
  el.style.opacity = String(0.2 + Math.random() * 0.4);
  el.style.top = `${Math.random() * 12}px`;
  const duracao = 6 + Math.random() * 8;
  el.style.animationDuration = `${duracao}s`;
  container.appendChild(el);
  setTimeout(() => el.remove(), duracao * 1000);
}

export function iniciarAnimacaoTopo(): void {
  const container = document.getElementById('stormContainer');
  if (!container) return;
  container.innerHTML = `
    <div class="kinetic-rail-line"></div>
    <div class="kinetic-pulse-beam"></div>
    <div class="kinetic-pulse-beam-rev"></div>
    <div class="kinetic-nodes-track" id="kineticNodesTrack"></div>`;
  const trilho = document.getElementById('kineticNodesTrack');
  NOS.forEach((no, i) => {
    const el = document.createElement('div');
    el.className = `kinetic-vector-node ${no.type}`;
    el.innerHTML = no.svg;
    el.style.animationDelay = `${(i * 0.45).toFixed(2)}s`;
    trilho?.appendChild(el);
  });
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  for (let i = 0; i < 40; i++) setTimeout(() => gerarIcone(container), i * 200);
  setInterval(() => gerarIcone(container), 400);
}
