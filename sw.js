/* WJ Ulm / Neu-Ulm — Service Worker
 *
 * Strategie:
 *   index.html / Navigationen  -> network-first  (Updates kommen sofort an,
 *                                 Cache nur als Offline-Rueckfall)
 *   termine.json               -> network-first  (moeglichst frische Termine)
 *   Fonts, Icons, SVG          -> cache-first    (aendern sich praktisch nie)
 *   alles Uebrige              -> stale-while-revalidate
 *
 * Der alte Worker war komplett cache-first. Dadurch bekam ein Geraet nach dem
 * ersten Besuch NIE wieder eine neue index.html zu sehen, solange der
 * Cache-Name unveraendert blieb.
 */

const VERSION = 'wj-ulm-v4';
const CORE = VERSION + '-core';
const RUNTIME = VERSION + '-runtime';

const PRECACHE = [
  './',
  './index.html',
  './manifest.json',
  './fonts/chivo-latin.woff2',
  './fonts/chivo-latin-ext.woff2',
  './fonts/bitter-latin.woff2',
  './fonts/bitter-latin-ext.woff2',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CORE)
      // einzeln, damit eine fehlende Datei nicht die ganze Installation kippt
      .then(cache => Promise.all(PRECACHE.map(u => cache.add(u).catch(() => null))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CORE && k !== RUNTIME).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// Erlaubt der Seite, ein Update sofort zu uebernehmen
self.addEventListener('message', event => {
  if (event.data === 'skipWaiting') self.skipWaiting();
});

function isFont(url)  { return /\.woff2?$/i.test(url.pathname) || url.pathname.startsWith('/fonts/'); }
function isImage(url) { return /\.(png|svg|ico|jpg|jpeg|webp)$/i.test(url.pathname); }

async function networkFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const fresh = await fetch(request);
    if (fresh && fresh.ok) cache.put(request, fresh.clone());
    return fresh;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) return cached;
    // Offline und nichts im Cache: bei Navigationen die Startseite zeigen
    if (request.mode === 'navigate') {
      const fallback = await caches.match('./index.html');
      if (fallback) return fallback;
    }
    throw err;
  }
}

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const cache = await caches.open(cacheName);
  const fresh = await fetch(request);
  if (fresh && fresh.ok) cache.put(request, fresh.clone());
  return fresh;
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const network = fetch(request)
    .then(res => { if (res && res.ok) cache.put(request, res.clone()); return res; })
    .catch(() => null);
  return cached || network.then(r => r || Promise.reject(new Error('offline')));
}

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Fremde Hosts (vereinonline, wjd.de, Google Maps ...) nie anfassen
  if (url.origin !== self.location.origin) return;

  if (request.mode === 'navigate' || url.pathname.endsWith('/index.html')) {
    event.respondWith(networkFirst(request, CORE));
    return;
  }
  if (url.pathname.endsWith('/termine.json')) {
    event.respondWith(networkFirst(request, RUNTIME));
    return;
  }
  if (isFont(url) || isImage(url)) {
    event.respondWith(cacheFirst(request, CORE));
    return;
  }
  event.respondWith(staleWhileRevalidate(request, RUNTIME));
});
