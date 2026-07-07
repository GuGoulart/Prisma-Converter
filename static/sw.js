const CACHE_NAME = 'prisma-cache-v3';
const ASSETS_TO_CACHE = [
  '/',
  '/static/style.css',
  '/static/script.js',
  '/static/manifest.json'
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
  // Ignore API requests and file downloads
  if (event.request.url.includes('/api/') || event.request.url.includes('/download/')) {
      return;
  }
  
  event.respondWith(
    fetch(event.request)
      .then(response => {
          // Atualiza o cache com a nova versão
          if (response && response.status === 200 && response.type === 'basic') {
              const responseToCache = response.clone();
              caches.open(CACHE_NAME).then(cache => {
                  cache.put(event.request, responseToCache);
              });
          }
          return response;
      })
      .catch(() => caches.match(event.request))
      .then(response => {
          // Se não houver rede nem cache, retorna a página inicial para navegações
          if (!response && event.request.mode === 'navigate') {
              return caches.match('/');
          }
          return response;
      })
  );
});
