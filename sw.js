/* The Vault — offline shell.
   Network first, always: if there is a connection the page you get is the
   published one, so republishing is never fought by a stale cache. Only when
   the network fails does the last good copy come out of the cupboard.
   The recordings are deliberately NOT cached — they are hundreds of megabytes
   and they are served from another origin with byte-range requests, which is
   how jumping to a timecode works at all. */
const BOX = 'vault-shell-v1';

self.addEventListener('install',  e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil((async () => {
  for (const k of await caches.keys()) if (k !== BOX) await caches.delete(k);
  await self.clients.claim();
})()));

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  if (req.headers.has('range')) return;                 // audio seeking
  let url; try { url = new URL(req.url); } catch (_) { return; }
  if (url.origin !== self.location.origin) return;      // audio + shared vault

  e.respondWith((async () => {
    try {
      const fresh = await fetch(req);
      if (fresh && fresh.ok) (await caches.open(BOX)).put(req, fresh.clone());
      return fresh;
    } catch (_) {
      const kept = await caches.match(req);
      if (kept) return kept;
      if (req.mode === 'navigate') {
        const shell = await caches.match('./');
        if (shell) return shell;
      }
      return new Response('Offline and nothing saved yet.', { status: 503 });
    }
  })());
});
