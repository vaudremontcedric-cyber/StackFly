# 💰 Coach Financier IA — Bêta

Application mobile PWA de coaching financier personnel, propulsée par Claude (Anthropic).

---

## 🚀 Installation rapide (en local)

### Prérequis
- Node.js 18+ installé (https://nodejs.org)
- Une clé API Anthropic (https://console.anthropic.com)

### Étapes

```bash
# 1. Aller dans le dossier
cd coach-financier

# 2. Installer les dépendances
npm install

# 3. Copier et configurer le fichier .env
copy .env.example .env
# → Ouvre .env et colle ta clé ANTHROPIC_API_KEY

# 4. Lancer l'application
npm start
```

L'app est disponible sur → **http://localhost:3000**

---

## 📱 Utiliser sur Android (même réseau WiFi)

1. Lance l'app sur ton PC (`npm start`)
2. Note ton IP locale : `ipconfig` → cherche "Adresse IPv4" (ex: 192.168.1.42)
3. Sur ton Android, ouvre Chrome et va sur : `http://192.168.1.42:3000`
4. Appuie sur le menu Chrome → **"Ajouter à l'écran d'accueil"**
5. L'app s'installe comme une vraie appli 🎉

---

## ☁️ Déploiement gratuit (pour partager avec d'autres)

### Option A : Railway (recommandé)
1. Va sur https://railway.app → Créer un compte
2. "New Project" → "Deploy from GitHub"
3. Upload ce dossier ou connecte un repo GitHub
4. Dans les variables d'environnement, ajoute : `ANTHROPIC_API_KEY=ta-clé`
5. L'app est en ligne avec une URL publique !

### Option B : Render
1. Va sur https://render.com → Créer un compte
2. "New Web Service" → connecte GitHub
3. Build Command : `npm install`
4. Start Command : `node server.js`
5. Ajoute la variable `ANTHROPIC_API_KEY` dans Environment

---

## 🔧 Structure du projet

```
coach-financier/
├── server.js          ← Serveur Node.js + proxy Claude API
├── package.json       ← Dépendances
├── .env               ← Ta clé API (ne pas partager !)
├── .env.example       ← Template de config
└── public/
    ├── index.html     ← Application PWA complète
    ├── manifest.json  ← Config PWA (icône, nom...)
    ├── sw.js          ← Service Worker (mode offline)
    └── icons/         ← Icônes de l'app
```

---

## 💡 Fonctionnalités

- **Chat avec le coach IA** — conversation naturelle en français
- **Dashboard automatique** — revenus, dépenses, reste à vivre détectés depuis le chat
- **Objectifs personnels** — liste de petits objectifs hebdomadaires
- **Mémoire de session** — le coach se souvient de la conversation
- **PWA** — s'installe sur Android comme une vraie app

---

## ⚠️ Notes importantes

- Les données sont stockées localement dans le navigateur
- L'API Anthropic a un coût à l'usage (très faible pour un usage personnel)
- Ne partage jamais ton fichier `.env` ni ta clé API
