const http   = require('http');
const https  = require('https');
const fs     = require('fs');
const path   = require('path');
const crypto = require('crypto');

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

// ─── RESET DE MOT DE PASSE PAR EMAIL (v5.118, Phase 2) ────────────────────
// Aucune base de donnees requise : les comptes vivent uniquement dans le
// localStorage de chaque utilisateur (cf_auth). Le serveur ne fait que
// prouver "cet email a bien recu ce code" via un jeton signe (HMAC) sans
// rien stocker lui-meme entre les deux appels /api/request-reset et
// /api/verify-reset - le client transporte le jeton (opaque pour lui).
//
// RESET_HMAC_SECRET : a definir en variable d'environnement Render pour que
// les jetons restent valides meme si le serveur redemarre entre les deux
// etapes. A defaut, un secret aleatoire est genere au demarrage (suffisant
// pour une seule instance Render qui ne redemarre pas en cours de route,
// mais deconseille en production - les codes deja envoyes deviendraient
// invalides si le serveur redemarre).
var RESET_HMAC_SECRET = process.env.RESET_HMAC_SECRET || crypto.randomBytes(32).toString('hex');
if (!process.env.RESET_HMAC_SECRET) {
  console.log('[RESET] ATTENTION : RESET_HMAC_SECRET non defini, secret aleatoire genere pour cette instance (voir commentaire serve.js).');
}
var BREVO_API_KEY    = process.env.BREVO_API_KEY || '';
var RESET_SENDER      = { name: 'RescueBudget', email: process.env.RESET_SENDER_EMAIL || 'rescuebudgetleo@gmail.com' };
var RESET_CODE_TTL_MS = 15 * 60000; // 15 minutes

// Anti-abus specifique au reset : separe du rate limit Gemini ci-dessus.
// Deux axes : par IP (empeche un script d'appeler l'endpoint en boucle) ET
// par email (empeche de spammer la boite mail d'une victime avec des codes
// qu'elle n'a jamais demandes, meme depuis des IP differentes).
var RESET_REQUEST_LIMIT_IP    = 8;  // demandes de code / heure / IP
var RESET_REQUEST_LIMIT_EMAIL = 4;  // demandes de code / heure / email
var RESET_VERIFY_LIMIT_IP     = 30; // tentatives de verification / heure / IP (code a 6 chiffres)
var _resetReqIp    = new Map();
var _resetReqEmail = new Map();
var _resetVerifyIp = new Map();

// Anti-abus pour l'email de bienvenue (v5.119) : memes principes que le
// reset ci-dessus (par IP ET par email), mais limites plus generreuses car
// aucun code sensible n'est en jeu ici - juste un email de confirmation.
// Autorise quelques reessais (ex: double-clic, page rechargee) sans ouvrir
// la porte a un envoi en masse vers des adresses arbitraires.
var WELCOME_LIMIT_IP    = 10; // envois / heure / IP
var WELCOME_LIMIT_EMAIL = 3;  // envois / heure / email
var _welcomeReqIp    = new Map();
var _welcomeReqEmail = new Map();

// Anti-abus pour le formulaire "Nous contacter" (v5.120) : le contenu est
// libre (message tape par le visiteur) et part directement dans la boite
// mail perso du developpeur - limites volontairement basses pour eviter
// qu'un usage malveillant ne la noie sous des messages automatises.
var CONTACT_DEST_EMAIL  = process.env.CONTACT_DEST_EMAIL || 'rescuebudgetleo@gmail.com';
var CONTACT_LIMIT_IP    = 8; // messages / heure / IP
var CONTACT_LIMIT_EMAIL = 4; // messages / heure / email (visiteur)
var _contactReqIp    = new Map();
var _contactReqEmail = new Map();

function checkHourlyLimit(map, key, limit) {
  var now = Date.now();
  var e = map.get(key);
  if (!e || now > e.resetAt) { e = { count: 0, resetAt: now + 3600000 }; map.set(key, e); }
  if (e.count >= limit) return false;
  e.count++;
  return true;
}

setInterval(function() {
  var now = Date.now();
  [_resetReqIp, _resetReqEmail, _resetVerifyIp, _welcomeReqIp, _welcomeReqEmail, _contactReqIp, _contactReqEmail].forEach(function(m) {
    m.forEach(function(v, k) { if (now > v.resetAt) m.delete(k); });
  });
}, 5 * 60000);

function readJsonBody(req, cb) {
  var body = '';
  var tooBig = false;
  req.on('data', function(chunk) {
    body += chunk.toString();
    if (body.length > 20000) { tooBig = true; } // garde-fou, ces routes n'ont besoin que de quelques octets
  });
  req.on('error', function() { cb(new Error('Erreur reseau')); });
  req.on('end', function() {
    if (tooBig) return cb(new Error('Corps de requete trop volumineux'));
    try { cb(null, body ? JSON.parse(body) : {}); }
    catch (e) { cb(new Error('JSON invalide')); }
  });
}

function isValidEmailServer(e) {
  return typeof e === 'string' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim()) && e.trim().length <= 254;
}

function genResetCode() {
  return String(crypto.randomInt(100000, 1000000)); // 6 chiffres, jamais de zero en tete ambigu
}

function computeResetToken(email, code, expiresAt) {
  return crypto.createHmac('sha256', RESET_HMAC_SECRET)
    .update(email.toLowerCase().trim() + '|' + code + '|' + expiresAt)
    .digest('hex');
}

function safeEqual(a, b) {
  var bufA = Buffer.from(String(a || ''));
  var bufB = Buffer.from(String(b || ''));
  if (bufA.length !== bufB.length) return false;
  return crypto.timingSafeEqual(bufA, bufB);
}

// Envoi via l'API transactionnelle Brevo (https://api.brevo.com/v3/smtp/email).
// Node 18+ expose fetch() globalement (voir package.json "engines").
// Fonction generique, factorisee (v5.119) pour etre reutilisee par le reset
// de mot de passe, l'email de bienvenue ET (v5.120) le formulaire de contact.
// extra (optionnel) : champs additionnels fusionnes dans le corps envoye a
// Brevo - utilise par le contact pour poser un replyTo vers l'email du
// visiteur, afin que repondre depuis la boite mail perso reponde bien a lui.
function sendBrevoEmail(toEmail, subject, htmlContent, extra) {
  var payload = {
    sender: RESET_SENDER,
    to: [{ email: toEmail }],
    subject: subject,
    htmlContent: htmlContent
  };
  if (extra) { for (var k in extra) { payload[k] = extra[k]; } }
  return fetch('https://api.brevo.com/v3/smtp/email', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'api-key': BREVO_API_KEY
    },
    body: JSON.stringify(payload)
  }).then(function(r) {
    if (!r.ok) {
      return r.text().then(function(t) {
        throw new Error('Brevo ' + r.status + ' : ' + t.slice(0, 300));
      });
    }
    return r.json().catch(function() { return {}; });
  });
}

function sendResetEmail(toEmail, code) {
  return sendBrevoEmail(toEmail, 'Ton code de reinitialisation RescueBudget',
    '<div style="font-family:sans-serif;max-width:480px;margin:0 auto">' +
    '<h2 style="color:#0d9488">RescueBudget</h2>' +
    '<p>Voici ton code pour reinitialiser ton mot de passe :</p>' +
    '<p style="font-size:32px;font-weight:700;letter-spacing:4px;background:#f1f5f9;padding:16px;border-radius:12px;text-align:center">' + code + '</p>' +
    '<p style="color:#64748b;font-size:13px">Ce code expire dans 15 minutes. Si tu n\'es pas a l\'origine de cette demande, ignore cet email : ton compte reste inchange.</p>' +
    '</div>'
  );
}

// Echappement minimal pour eviter d'injecter du HTML si le pseudo contient
// des caracteres speciaux (le pseudo vient de l'utilisateur, jamais verifie
// cote serveur puisque tout est stocke en local - on reste prudent quand on
// le reinjecte dans un email HTML).
function escapeHtml(s) {
  return String(s || '').replace(/[&<>"']/g, function(c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
}

// Email de bienvenue (v5.119) : envoye une seule fois, juste apres la
// creation du compte cote client. Purement informatif - confirme que
// l'adresse saisie est valide et joignable, rassure sur la confidentialite
// des donnees (qui restent locales). Aucun lien d'action, aucune donnee
// sensible dedans : contrairement au reset, un echec d'envoi n'a aucune
// consequence sur le compte (deja cree localement avant cet appel).
function sendWelcomeEmail(toEmail, username) {
  var safeName = escapeHtml(username);
  return sendBrevoEmail(toEmail, 'Bienvenue sur RescueBudget !',
    '<div style="font-family:sans-serif;max-width:480px;margin:0 auto">' +
    '<h2 style="color:#0d9488">RescueBudget</h2>' +
    '<p>Salut ' + safeName + ' 👋</p>' +
    '<p>Ton compte RescueBudget vient d\'etre cree avec cette adresse email. Elle nous sert uniquement a t\'envoyer un code si tu demandes un jour a reinitialiser ton mot de passe.</p>' +
    '<p style="color:#64748b;font-size:13px">Pour rappel : toutes tes donnees financieres (depenses, revenus, enveloppes...) restent uniquement sur ton appareil, jamais sur un serveur.</p>' +
    '<p style="color:#64748b;font-size:13px">Si tu n\'es pas a l\'origine de cette creation de compte, tu peux ignorer cet email.</p>' +
    '</div>'
  );
}

// Formulaire "Nous contacter" (v5.120) : transmet le message d'un
// utilisateur vers la boite mail perso du developpeur (CONTACT_DEST_EMAIL).
// Pas de reponse in-app : replyTo pointe vers l'email du visiteur pour que
// repondre depuis n'importe quel client mail arrive directement chez lui.
function sendContactEmail(fromEmail, fromUser, message) {
  var safeUser = escapeHtml(fromUser || 'Utilisateur anonyme');
  var safeMsg  = escapeHtml(message).replace(/\n/g, '<br>');
  return sendBrevoEmail(CONTACT_DEST_EMAIL, 'RescueBudget - Message de ' + (fromUser || fromEmail),
    '<div style="font-family:sans-serif;max-width:560px;margin:0 auto">' +
    '<h2 style="color:#0d9488">RescueBudget - Nouveau message</h2>' +
    '<p><b>De :</b> ' + safeUser + ' (' + escapeHtml(fromEmail) + ')</p>' +
    '<div style="background:#f1f5f9;padding:16px;border-radius:12px;margin-top:12px;white-space:pre-wrap">' + safeMsg + '</div>' +
    '<p style="color:#64748b;font-size:13px;margin-top:16px">Reponds directement a cet email pour contacter l\'utilisateur.</p>' +
    '</div>',
    { replyTo: { email: fromEmail, name: fromUser || undefined } }
  );
}

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

  // ─── RESET MOT DE PASSE : demande de code (etape 1/2) ─────────────
  if (req.method === 'POST' && req.url === '/api/request-reset') {
    var rrIp = getClientIp(req);

    if (!BREVO_API_KEY) {
      console.log('[RESET] BREVO_API_KEY non configuree, requete refusee');
      res.writeHead(503, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
      res.end(JSON.stringify({ error: 'Service de reinitialisation par email non configure sur ce serveur.' }));
      return;
    }

    readJsonBody(req, function(err, data) {
      if (err) {
        res.writeHead(400, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ error: err.message }));
        return;
      }
      var email = (data && data.email ? String(data.email) : '').trim();
      if (!isValidEmailServer(email)) {
        res.writeHead(400, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ error: 'Adresse email invalide' }));
        return;
      }
      if (!checkHourlyLimit(_resetReqIp, rrIp, RESET_REQUEST_LIMIT_IP) ||
          !checkHourlyLimit(_resetReqEmail, email.toLowerCase(), RESET_REQUEST_LIMIT_EMAIL)) {
        console.log('[RESET] Rate limit demande de code depasse pour ' + rrIp + ' / ' + email);
        res.writeHead(429, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ error: 'Trop de demandes. Reessaie dans un instant.' }));
        return;
      }

      var code      = genResetCode();
      var expiresAt = Date.now() + RESET_CODE_TTL_MS;
      var token     = computeResetToken(email, code, expiresAt);

      sendResetEmail(email, code).then(function() {
        console.log('[RESET] Code envoye a ' + email);
        res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ ok: true, token: token, expiresAt: expiresAt }));
      }).catch(function(e) {
        console.log('[RESET] Erreur envoi email: ' + e.message);
        res.writeHead(502, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ error: 'Impossible d\'envoyer l\'email pour le moment. Reessaie plus tard.' }));
      });
    });
    return;
  }

  // ─── RESET MOT DE PASSE : verification du code (etape 2/2) ────────
  if (req.method === 'POST' && req.url === '/api/verify-reset') {
    var rvIp = getClientIp(req);
    if (!checkHourlyLimit(_resetVerifyIp, rvIp, RESET_VERIFY_LIMIT_IP)) {
      console.log('[RESET] Rate limit verification depasse pour ' + rvIp);
      res.writeHead(429, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
      res.end(JSON.stringify({ error: 'Trop de tentatives. Redemande un code.' }));
      return;
    }

    readJsonBody(req, function(err, data) {
      if (err) {
        res.writeHead(400, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ error: err.message }));
        return;
      }
      var email     = (data && data.email ? String(data.email) : '').trim();
      var code      = (data && data.code ? String(data.code) : '').trim();
      var token     = (data && data.token ? String(data.token) : '').trim();
      var expiresAt = data && data.expiresAt ? Number(data.expiresAt) : 0;

      if (!email || !code || !token || !expiresAt) {
        res.writeHead(400, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ error: 'Requete incomplete' }));
        return;
      }
      if (Date.now() > expiresAt) {
        res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ ok: false, error: 'Code expire, redemande-en un nouveau.' }));
        return;
      }
      var expected = computeResetToken(email, code, expiresAt);
      if (!safeEqual(expected, token)) {
        res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ ok: false, error: 'Code incorrect.' }));
        return;
      }
      res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
      res.end(JSON.stringify({ ok: true }));
    });
    return;
  }

  // ─── EMAIL DE BIENVENUE (v5.119) : envoye a la creation du compte ─
  if (req.method === 'POST' && req.url === '/api/send-welcome') {
    var wIp = getClientIp(req);

    if (!BREVO_API_KEY) {
      console.log('[WELCOME] BREVO_API_KEY non configuree, envoi ignore');
      res.writeHead(503, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
      res.end(JSON.stringify({ error: 'Service email non configure sur ce serveur.' }));
      return;
    }

    readJsonBody(req, function(err, data) {
      if (err) {
        res.writeHead(400, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ error: err.message }));
        return;
      }
      var email = (data && data.email ? String(data.email) : '').trim();
      var user  = (data && data.user  ? String(data.user)  : '').trim().slice(0, 60);
      if (!isValidEmailServer(email)) {
        res.writeHead(400, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ error: 'Adresse email invalide' }));
        return;
      }
      if (!checkHourlyLimit(_welcomeReqIp, wIp, WELCOME_LIMIT_IP) ||
          !checkHourlyLimit(_welcomeReqEmail, email.toLowerCase(), WELCOME_LIMIT_EMAIL)) {
        console.log('[WELCOME] Rate limit depasse pour ' + wIp + ' / ' + email);
        res.writeHead(429, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ error: 'Trop de demandes.' }));
        return;
      }

      sendWelcomeEmail(email, user || 'toi').then(function() {
        console.log('[WELCOME] Email de bienvenue envoye a ' + email);
        res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ ok: true }));
      }).catch(function(e) {
        console.log('[WELCOME] Erreur envoi email: ' + e.message);
        res.writeHead(502, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ error: 'Impossible d\'envoyer l\'email pour le moment.' }));
      });
    });
    return;
  }

  // ─── FORMULAIRE "NOUS CONTACTER" (v5.120) ─────────────────────────
  if (req.method === 'POST' && req.url === '/api/contact') {
    var cIp = getClientIp(req);

    if (!BREVO_API_KEY) {
      console.log('[CONTACT] BREVO_API_KEY non configuree, envoi ignore');
      res.writeHead(503, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
      res.end(JSON.stringify({ error: 'Service de contact non configure sur ce serveur.' }));
      return;
    }

    readJsonBody(req, function(err, data) {
      if (err) {
        res.writeHead(400, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ error: err.message }));
        return;
      }
      var email   = (data && data.email   ? String(data.email)   : '').trim();
      var user    = (data && data.user    ? String(data.user)    : '').trim().slice(0, 60);
      var message = (data && data.message ? String(data.message) : '').trim();

      if (!isValidEmailServer(email)) {
        res.writeHead(400, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ error: 'Adresse email invalide' }));
        return;
      }
      if (message.length < 3 || message.length > 4000) {
        res.writeHead(400, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ error: 'Message trop court ou trop long (max 4000 caracteres)' }));
        return;
      }
      if (!checkHourlyLimit(_contactReqIp, cIp, CONTACT_LIMIT_IP) ||
          !checkHourlyLimit(_contactReqEmail, email.toLowerCase(), CONTACT_LIMIT_EMAIL)) {
        console.log('[CONTACT] Rate limit depasse pour ' + cIp + ' / ' + email);
        res.writeHead(429, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ error: 'Trop de messages envoyes. Reessaie plus tard.' }));
        return;
      }

      sendContactEmail(email, user, message).then(function() {
        console.log('[CONTACT] Message transmis (de ' + email + ')');
        res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ ok: true }));
      }).catch(function(e) {
        console.log('[CONTACT] Erreur envoi email: ' + e.message);
        res.writeHead(502, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ error: 'Impossible d\'envoyer le message pour le moment. Reessaie plus tard.' }));
      });
    });
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
