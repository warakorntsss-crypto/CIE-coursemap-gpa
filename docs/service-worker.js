// Caches the app SHELL so it loads instantly / works offline. Data calls are
// NEVER cached: any /api/ request and any cross-origin request (the Google
// Apps Script /exec endpoint lives on script.google.com) always go to the
// network so progress data stays live.
//
// index.html and data.js are NETWORK-FIRST: a pure cache-first shell meant a
// deployed fix could stay invisible for a long time, because the cached copy
// was served forever and even a version bump could re-cache stale bytes out of
// the browser's own HTTP cache. They now come from the network whenever the
// device is online, and fall back to the cache offline. Icons and the manifest
// stay cache-first (they rarely change and are the slow part of a cold start).
const CACHE = "coursemaps-cie-shell-v35";
const SHELL = [
  "./", "./index.html", "./data.js", "./manifest.json",
  "./icon-192.png", "./icon-512.png"
];
// documents + code: always try the network first
const isFresh = (url) => url.pathname === "/" ||
  /\/(index\.html|data\.js)$/.test(url.pathname) || url.pathname.endsWith("/");

self.addEventListener("install", (e) => {
  // {cache:"reload"} bypasses the browser HTTP cache so the shell we store is
  // the freshly deployed one, not whatever the browser happens to be holding.
  e.waitUntil(caches.open(CACHE).then((c) =>
    c.addAll(SHELL.map((u) => new Request(u, { cache: "reload" })))));
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

  if (e.request.mode === "navigate" || isFresh(url)) {
    // {cache:"reload"} here for the SAME reason as in install: GitHub Pages serves the shell
    // with Cache-Control: max-age=600, so a plain fetch() can be answered from the BROWSER's
    // own HTTP cache and hand back a pre-deploy index.html or data.js -- which then got
    // written into the current cache below and outlived the 600s. That produced a MIXED
    // build (new index.html calling API.setCustom against an old data.js that has no such
    // method), which is not a theoretical risk: it was observed live right after v30.
    e.respondWith(
      fetch(new Request(e.request, { cache: "reload" })).then((res) => {
        // never store an error page as if it were the shell
        if (res && res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(e.request, copy)); }
        return res;
      }).catch(() => caches.match(e.request).then((hit) =>
        hit || caches.match("./index.html")))
    );
    return;
  }
  e.respondWith(
    caches.match(e.request).then((hit) =>
      hit || fetch(e.request).then((res) => {
        if (res && res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(e.request, copy)); }
        return res;
      }).catch(() => hit))
  );
});
