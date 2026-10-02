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

// Alle Mini-Apps liegen auf derselben Herkunft (mvonulmerbach-ship-it.github.io)
// und teilen sich EINEN Cache-Speicher. Darum tragen die Cache-Namen das
// Praefix "wj-ulm-app::" und beim Aktivieren werden nur eigene Caches
// geloescht -- niemals die anderer Apps. "::" als Trenner, damit ein
// Praefix nie den Namen einer anderen App mit gleichem Anfang trifft.
const PRAEFIX = 'wj-ulm-app::';
const ALT_PRAEFIXE = ['wj-ulm-v'];   // fruehere Cache-Namen (wj-ulm-v4-core ...)
const CORE = PRAEFIX + 'core-v6';
const RUNTIME = PRAEFIX + 'runtime-v6';

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
      // cache:'reload': am HTTP-Cache des Browsers vorbei - sonst landet nach einem Update
      // eine noch frische alte index.html im neuen Cache (gemessen 02.10.2026)
      .then(cache => Promise.all(PRECACHE.map(u => cache.add(new Request(u, { cache: 'reload' })).catch(() => null))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(k => (k.startsWith(PRAEFIX) && k !== CORE && k !== RUNTIME) ||
                       ALT_PRAEFIXE.some(a => k.startsWith(a)))
          .map(k => caches.delete(k))
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
      const fallback = await (await caches.open(CORE)).match('./index.html');
      if (fallback) return fallback;
    }
    throw err;
  }
}

async function cacheFirst(request, cacheName) {
  // nur im eigenen Cache suchen -- caches.match wuerde alle Apps durchsuchen
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  if (cached) return cached;
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

  // Nur Dateien dieser App: fremde Hosts (vereinonline, wjd.de, Google Maps ...)
  // und die anderen Apps auf derselben Herkunft nie anfassen
  if (!request.url.startsWith(self.registration.scope)) return;

  const url = new URL(request.url);

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
