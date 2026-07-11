const http  = require('http');
const https = require('https');
const fs    = require('fs');
const path  = require('path');

const PORT = process.env.PORT || 8080;
const DIR  = __dirname;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css':  'text/css',
  '.js':   'application/javascript',
  '.json': 'application/json',
  '.png':  'image/png',
  '.ico':  'image/x-icon'
};

// Evite que le serveur crashe sur une erreur non geree
process.on('uncaughtException', function(err) {
  console.log('\n[ERREUR] ' + err.message);
  console.log(err.stack);
  console.log('[INFO] Le serveur continue de fonctionner.\n');
});

// ─── RATE LIMITING ANTI-ABUS (protege le quota Gemini gratuit partage) ───
// Sans ca, /api/gemini est un endpoint totalement ouvert : n'importe qui
// (script, bot, scraper) qui trouve l'URL Render peut l'appeler directement,
// hors de l'appli, et consommer a lui seul tout le quota gratuit journalier
// partage entre TOUS les vrais utilisateurs. En memoire (pas de DB requise
// pour une simple protection anti-abus) ; reset naturel au redemarrage du
// serveur, ce qui est acceptable pour cet usage.
var RATE_LIMIT_PER_MIN = 15;   // tres au-dessus du rythme d'une vraie conversation humaine
var RATE_LIMIT_PER_DAY = 300;  // evite qu'une seule IP ne vide le quota gratuit journalier partage
var _rlMinute = new Map(); // ip -> {count, resetAt}
var _rlDay    = new Map(); // ip -> {count, resetAt}

function getClientIp(req) {
  var fwd = req.headers['x-forwarded-for'];
  if (fwd) return fwd.split(',')[0].trim(); // Render (et la plupart des PaaS) passent l'IP reelle ici
  return (req.socket && req.socket.remoteAddress) || 'unknown';
}

function checkRateLimit(ip) {
  var now = Date.now();
  var min = _rlMinute.get(ip);
  if (!min || now > min.resetAt) { min = { count: 0, resetAt: now + 60000 }; _rlMinute.set(ip, min); }
  var day = _rlDay.get(ip);
  if (!day || now > day.resetAt) { day = { count: 0, resetAt: now + 86400000 }; _rlDay.set(ip, day); }
  if (min.count >= RATE_LIMIT_PER_MIN) return { ok: false, reason: 'par minute' };
  if (day.count >= RATE_LIMIT_PER_DAY) return { ok: false, reason: 'par jour' };
  min.count++; day.count++;
  return { ok: true };
}

// Nettoyage periodique pour eviter une fuite memoire sur le long terme
setInterval(function() {
  var now = Date.now();
  _rlMinute.forEach(function(v, k) { if (now > v.resetAt) _rlMinute.delete(k); });
  _rlDay.forEach(function(v, k) { if (now > v.resetAt) _rlDay.delete(k); });
}, 5 * 60000);

// Parse manuellement les query params (compatible toutes versions Node.js)
function parseQuery(url) {
  var idx = url.indexOf('?');
  if (idx < 0) return {};
  var qs = url.slice(idx + 1);
  var params = {};
  qs.split('&').forEach(function(pair) {
    var eq = pair.indexOf('=');
    if (eq < 0) return;
    var k = pair.slice(0, eq);
    var v = pair.slice(eq + 1);
    try { params[k] = decodeURIComponent(v); } catch(e) { params[k] = v; }
  });
  return params;
}

var server = http.createServer(function(req, res) {

  // ─── Test de connectivite ────────────────────────────────────────
  if (req.method === 'GET' && req.url === '/api/ping') {
    console.log('[PING] Test de connexion OK');
    res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
    res.end(JSON.stringify({ status: 'ok', proxy: true, version: '2.0' }));
    return;
  }

  // ─── PROXY Gemini API ────────────────────────────────────────────
  if (req.method === 'POST' && req.url.indexOf('/api/gemini') === 0) {
    console.log('[PROXY] Requete recue');

    var clientIp = getClientIp(req);
    var rl = checkRateLimit(clientIp);
    if (!rl.ok) {
      console.log('[PROXY] Rate limit depasse (' + rl.reason + ') pour ' + clientIp);
      res.writeHead(429, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
      res.end(JSON.stringify({ error: { message: 'Trop de requetes depuis cette adresse (limite ' + rl.reason + '). Reessaie dans un instant. (429)' } }));
      return;
    }

    var params  = parseQuery(req.url);
    var model   = params['model']  || 'gemini-1.5-flash';
    var apiVer  = params['apiver'] || 'v1beta';
    // SÉCURITÉ + COÛT : priorité à la clé PERSO de l'utilisateur (en-tête x-api-key,
    // jamais dans l'URL) quand il en a configuré une — ça décharge d'autant le
    // quota gratuit partagé de la clé serveur. À défaut, clé serveur (variable
    // d'environnement Render : GEMINI_API_KEY), pour que l'appli fonctionne sans
    // rien configurer. Le paramètre ?key= reste accepté uniquement pour
    // compatibilité avec d'anciennes versions.
    var key = req.headers['x-api-key'] || process.env.GEMINI_API_KEY || params['key'] || '';

    if (!key) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: { message: 'Cle API manquante' } }));
      return;
    }

    var body = '';
    req.on('error', function(err) { console.log('[PROXY] Erreur requete: ' + err.message); });
    req.on('data', function(chunk) { body += chunk.toString(); });
    req.on('end', function() {
      console.log('[PROXY] Corps recu, appel Google...');

      var bodyBuf = Buffer.from(body, 'utf8');
      var options = {
        hostname: 'generativelanguage.googleapis.com',
        port: 443,
        path: '/' + apiVer + '/models/' + encodeURIComponent(model) + ':generateContent?key=' + encodeURIComponent(key),
        method: 'POST',
        headers: {
          'Content-Type':   'application/json',
          'Content-Length': bodyBuf.length
        }
      };

      var responded = false;

      var proxyReq = https.request(options, function(pres) {
        console.log('[PROXY] Reponse Google: ' + pres.statusCode);
        var chunks = [];
        pres.on('data', function(c) { chunks.push(c); });
        pres.on('end', function() {
          if (responded) return;
          responded = true;
          try {
            var data = Buffer.concat(chunks);
            res.writeHead(pres.statusCode, {
              'Content-Type':  'application/json',
              'Access-Control-Allow-Origin': '*'
            });
            res.end(data);
          } catch(e) {
            console.log('[PROXY] Erreur envoi reponse: ' + e.message);
          }
        });
        pres.on('error', function(err) {
          console.log('[PROXY] Erreur reponse: ' + err.message);
        });
      });

      proxyReq.on('error', function(err) {
        console.log('[PROXY] Erreur connexion Google: ' + err.message);
        if (responded) return;
        responded = true;
        try {
          res.writeHead(502, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: { message: 'Proxy error: ' + err.message } }));
        } catch(e) {}
      });

      proxyReq.setTimeout(58000, function() {
        console.log('[PROXY] Timeout 58s');
        proxyReq.destroy();
        if (responded) return;
        responded = true;
        try {
          res.writeHead(504, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
          res.end(JSON.stringify({ error: { message: 'Timeout: Google API trop lente' } }));
        } catch(e) {}
      });

      proxyReq.write(bodyBuf);
      proxyReq.end();
    });
    return;
  }

  // Preflight CORS
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin':  '*',
      'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    });
    res.end();
    return;
  }

  // ─── Fichiers statiques ──────────────────────────────────────────
  var urlPath = req.url.split('?')[0];
  var filePath = urlPath === '/' ? '/CoachFinancier.html' : urlPath;
  filePath = path.join(DIR, filePath);

  fs.readFile(filePath, function(err, data) {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Fichier non trouve : ' + req.url);
      return;
    }
    var ext  = path.extname(filePath);
    var mime = MIME[ext] || 'text/plain';
    var headers = { 'Content-Type': mime };
    // Ne jamais mettre le HTML en cache (évite les conflits avec le SW)
    if (ext === '.html' || filePath.endsWith('CoachFinancier.html')) {
      headers['Cache-Control'] = 'no-cache, no-store, must-revalidate';
      headers['Pragma'] = 'no-cache';
    }
    res.writeHead(200, headers);
    res.end(data);
  });
});

server.listen(PORT, '0.0.0.0', function() {
  var os      = require('os');
  var ifaces  = os.networkInterfaces();
  var localIP = 'ton-ip-locale';
  Object.values(ifaces).forEach(function(list) {
    list.forEach(function(iface) {
      if (iface.family === 'IPv4' && !iface.internal) localIP = iface.address;
    });
  });

  console.log('\n================================================');
  console.log('   StackFly - Serveur demarre (v2 + proxy)');
  console.log('================================================');
  console.log('\n  Sur ce PC :');
  console.log('  --> http://localhost:' + PORT);
  console.log('\n  Sur ton Android (meme WiFi) :');
  console.log('  --> http://' + localIP + ':' + PORT);
  console.log('\n  Presse Ctrl+C pour arreter');
  console.log('================================================\n');
});

server.on('error', function(err) {
  if (err.code === 'EADDRINUSE') {
    console.log('\n[ERREUR] Le port ' + PORT + ' est deja utilise !');
    console.log('Ferme la fenetre noire precedente, puis relance ce fichier.\n');
  } else {
    console.log('\n[ERREUR SERVEUR] ' + err.message);
  }
  process.exit(1);
});
