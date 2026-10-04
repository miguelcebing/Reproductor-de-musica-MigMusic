/* MigMusic service worker: offline app shell and static asset cache.
 *
 * It deliberately NEVER caches `/api/*`: playlists, lyrics and session-scoped
 * data are private and must always come from the network. Cross-origin
 * requests (YouTube IFrame, Spotify SDK, cover images) are left to the browser
 * so their own caching and CORS rules apply.
 */

const CACHE_NAME = "migmusic-static-v2";
const APP_SHELL = [
  "/",
  "/index.html",
  "/manifest.webmanifest",
  "/spotify-ready.js",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "/icons/apple-touch-icon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return; // CDNs: browser handles them
  if (url.pathname.startsWith("/api/")) return; // private data: never cached

  if (request.mode === "navigate") {
    event.respondWith(networkFirst(request));
    return;
  }
  event.respondWith(staleWhileRevalidate(request));
});

/** Navigation: fresh HTML when online, the cached shell when offline. */
async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  try {
    const response = await fetch(request);
    if (response.ok) cache.put("/index.html", response.clone());
    return response;
  } catch {
    const cached = await cache.match("/index.html");
    return cached ?? Response.error();
  }
}

/** Static assets: serve the cache instantly and refresh it in the background. */
async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  const network = fetch(request)
    .then((response) => {
      if (response.ok) cache.put(request, response.clone());
      return response;
    })
    .catch(() => cached ?? Response.error());
  return cached ?? network;
}
