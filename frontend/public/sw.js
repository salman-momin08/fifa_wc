/**
 * FIFA WC 2026 Stadium Operations — Service Worker
 * Provides offline-first caching for static assets, API fallbacks,
 * and emergency offline guidance.
 */

const CACHE_VERSION = "fifa-wc-v2";
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const API_CACHE = `${CACHE_VERSION}-api`;

const STATIC_ASSETS = [
  "/",
  "/_next/static/",
];

const API_ROUTES_TO_CACHE = [
  "/api/crowd/status",
  "/api/transport/status",
  "/api/decision/list",
  "/api/sustainability/nudge",
];

// ── Install: pre-cache static assets ─────────────────────────────────────────
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {
        // Non-fatal — continue install even if some assets fail
      });
    })
  );
  self.skipWaiting();
});

// ── Activate: clean up old caches ────────────────────────────────────────────
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) =>
      Promise.all(
        cacheNames
          .filter((name) => name.startsWith("fifa-wc-") && name !== STATIC_CACHE && name !== API_CACHE)
          .map((name) => caches.delete(name))
      )
    )
  );
  self.clients.claim();
});

// ── Fetch: network-first for API, cache-first for static ─────────────────────
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and WebSocket requests
  if (request.method !== "GET" || url.protocol === "ws:" || url.protocol === "wss:") {
    return;
  }

  // API routes: network-first with cache fallback
  if (API_ROUTES_TO_CACHE.some((route) => url.pathname.includes(route))) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.status === 200) {
            const cloned = response.clone();
            caches.open(API_CACHE).then((cache) => cache.put(request, cloned));
          }
          return response;
        })
        .catch(() =>
          caches.match(request).then(
            (cached) =>
              cached ||
              new Response(
                JSON.stringify({ error: "Offline", message: "Data unavailable offline." }),
                { headers: { "Content-Type": "application/json" } }
              )
          )
        )
    );
    return;
  }

  // Static assets: cache-first
  event.respondWith(
    caches.match(request).then(
      (cached) => cached || fetch(request).catch(() => caches.match("/"))
    )
  );
});
