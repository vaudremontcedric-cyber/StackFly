# 🆘 RescueBudget

**Outil pédagogique de gestion budgétaire avec coach IA.**
Quand ton pouvoir d'achat disparaît, RescueBudget intervient.

> ⚖️ RescueBudget est un outil d'éducation budgétaire. Il ne fournit **aucun conseil en
> investissement** ni recommandation personnalisée de placement. Pour tout projet
> d'investissement, consultez un professionnel habilité (CIF immatriculé ORIAS).

## Fonctionnalités
- 📊 Budget selon la méthode 50/30/20 (besoins / envies / épargne)
- 💬 Coach IA « Léo » (Google Gemini) — pédagogique, jamais culpabilisant
- 🎯 Objectifs d'épargne avec suivi de progression
- 🔁 Suivi des abonnements et transactions
- 🏅 Gamification : badges, streaks, niveaux
- 📴 PWA : fonctionne hors-ligne, installable sur mobile
- 🆘 Bouton SOS : ressources officielles gratuites (Banque de France, Points Conseil Budget, Crésus, 115)
- 🔒 Données 100 % locales par défaut (localStorage) — export/sauvegarde JSON et CSV

## Démarrage

### En local
```bash
node serve.js
# puis ouvrir http://localhost:8080
```

### Déploiement Render
1. Connecter le dépôt GitHub à Render (service web Node).
2. **Important — clé API côté serveur** : dans Render → *Environment*, ajouter la
   variable **`GEMINI_API_KEY`** avec votre clé Google AI Studio.
   Les utilisateurs n'ont alors **rien à configurer** : le coach fonctionne immédiatement.
3. Commande de démarrage : `node serve.js` (port fourni par Render via `PORT`).

## Sécurité
- Mots de passe hachés en **SHA-256** (Web Crypto) — migration automatique des anciens comptes à la première connexion.
- La clé API Gemini n'apparaît **jamais dans les URL** (variable d'environnement côté serveur, ou en-tête `x-api-key`).
- Ne jamais committer de clé dans le dépôt (`.gitignore` bloque les `.env`).
- ⚠️ Synchronisation cloud Firebase : fonctionnalité expérimentale. Sans règles de sécurité
  Firestore strictes, les données sont accessibles à quiconque devine l'identifiant.
  À réserver aux tests, ou à sécuriser avec Firebase Auth avant tout usage réel.

## Nettoyage du dépôt (recommandé)
Le dossier historique contient des captures d'écran et scripts locaux (~50 Mo).
Après ajout du `.gitignore` :
```bash
git rm -r --cached .
git add .
git commit -m "Nettoyage du dépôt + .gitignore"
```

## Licence & contact
Projet personnel en développement — © RescueBudget.
