const CACHE_NAME = 'prisma-cache-v2';
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
    caches.match(event.request)
      .then(response => response || fetch(event.request))
      .catch(() => {
          if (event.request.mode === 'navigate') {
              return caches.match('/');
          }
      })
  );
});
