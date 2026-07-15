// Service Worker — RescueBudget (mise en cache hors-ligne)
// v5.136 : ce fichier remplace l'ancien Service Worker construit en memoire sous forme de
// Blob (voir CoachFinancier.html avant v5.136). Bug trouve en verifiant la console du site en
// production : navigator.serviceWorker.register() rejette categoriquement les URL blob: comme
// script - erreur "The URL protocol of the script (...) is not supported" - ce qui faisait que
// le Service Worker n'a JAMAIS reussi a s'enregistrer, sur aucun navigateur, depuis sa creation.
// L'appli fonctionnait normalement (aucune fonctionnalite visible ne depend du SW), mais tout le
// travail de mise en cache hors-ligne etait silencieusement inoperant. Un vrai fichier statique
// comme celui-ci est la seule maniere valide d'enregistrer un Service Worker.
//
// La version est passee en query string par CoachFinancier.html au moment de l'enregistrement
// (navigator.serviceWorker.register('./sw.js?v='+APP_VERSION)) : elle change a chaque nouvelle
// version de l'app pour invalider proprement le cache precedent.
var CACHE = 'rb-cache-v' + (new URL(self.location.href).searchParams.get('v') || '0');

self.addEventListener('install', function(e) {
  e.waitUntil(caches.open(CACHE).then(function(c) {
    return c.addAll(['./', './CoachFinancier.html']);
  }).catch(function() {}));
  self.skipWaiting();
});

self.addEventListener('activate', function(e) {
  e.waitUntil(caches.keys().then(function(keys) {
    return Promise.all(keys.filter(function(k) { return k !== CACHE; }).map(function(k) { return caches.delete(k); }));
  }));
  self.clients.claim();
});

self.addEventListener('fetch', function(e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  if (req.url.indexOf('/api/') > -1 || req.url.indexOf('generativelanguage') > -1) return;
  e.respondWith(
    fetch(req).then(function(resp) {
      var clone = resp.clone();
      caches.open(CACHE).then(function(c) { c.put(req, clone); });
      return resp;
    }).catch(function() {
      return caches.match(req);
    })
  );
});
