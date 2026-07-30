const CACHE_NAME = 'prisma-cache-v7';
const ASSETS_TO_CACHE = [
  '/',
  '/static/style.css',
  '/static/i18n.js',
  '/static/script.js',
  '/static/pdf_tools.js',
  '/static/file_tools.js',
  '/static/css/vars.css',
  '/static/css/layout.css',
  '/static/css/components.css',
  '/static/css/animations.css',
  '/static/manifest.json',
  '/static/favicon.svg',
  '/static/icon-192.png',
  '/static/icon-512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS_TO_CACHE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cache => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Ignorar requisições de domínios externos (ex: Google Fonts)
  if (url.origin !== self.location.origin) return;

  // PERF-006: Ignora rotas dinâmicas (sessão Flask) e de API/download
  const rotasDinamicas = ['/', '/conversor', '/upload', '/converter', '/preview', '/ferramentas-avancadas', '/modificar-arquivos'];
  const isDinamica = rotasDinamicas.some(r => url.pathname === r || url.pathname.startsWith('/preview/'));
  if (isDinamica || url.pathname.includes('/api/') || url.pathname.includes('/download/')) {
      return;
  }

  event.respondWith(
    fetch(event.request)
      .then(response => {
          // Atualiza o cache com a nova versão
          if (response && response.status === 200 && (response.type === 'basic' || response.type === 'cors')) {
              const responseToCache = response.clone();
              caches.open(CACHE_NAME).then(cache => {
                  cache.put(event.request, responseToCache);
              }).catch(() => {});
          }
          return response;
      })
      .catch(() => caches.match(event.request))
      .then(response => {
          if (response) {
              return response;
          }
          // Se não houver rede nem cache, retorna a página inicial para navegações
          if (event.request.mode === 'navigate') {
              return caches.match('/');
          }
          return new Response('', { status: 404, statusText: 'Not Found' });
      })
  );
});
