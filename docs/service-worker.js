// Caches the app SHELL so it loads instantly / works offline. Data calls are
// NEVER cached: any /api/ request and any cross-origin request (the Google
// Apps Script /exec endpoint lives on script.google.com) always go to the
// network so progress data stays live.
const CACHE = "coursemaps-cie-shell-v6";
const SHELL = [
  "./", "./index.html", "./data.js", "./manifest.json",
  "./icon-192.png", "./icon-512.png"
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) =>
    Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  // never intercept data calls or cross-origin requests (Apps Script /exec)
  if (e.request.method !== "GET" || url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/")) return;
  e.respondWith(
    caches.match(e.request).then((hit) =>
      hit || fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      }).catch(() => hit))
  );
});
