# RescueBudget — Plan de coût API Gemini
**Dernière mise à jour : juillet 2026**

---

## 1. Le point le plus important : le Free Tier ne coûte jamais rien

Confirmé sur la doc officielle Google ([ai.google.dev/gemini-api/docs/billing](https://ai.google.dev/gemini-api/docs/billing)) :

> Tant qu'aucun compte de facturation n'est lié au projet Google AI Studio utilisé pour `GEMINI_API_KEY`, le projet reste sur le **Free Tier**. Il n'y a **aucun montant facturable possible** sur ce tier — le pire qui puisse arriver est un blocage temporaire par quota (erreur 429), jamais une facture surprise.

**Recommandation : ne PAS lier de compte de facturation au projet tant que l'app n'a pas une traction réelle et un modèle de revenu pour l'absorber.** C'est la décision structurante n°1 — elle fixe le risque financier à 0€ par construction, quel que soit le nombre d'utilisateurs.

---

## 2. Tarifs (si un jour vous passez en payant)

| Modèle | Entrée (input) | Sortie (output) |
|---|---|---|
| gemini-2.5-flash (utilisé par défaut) | 0,30 $ / 1M tokens | 2,50 $ / 1M tokens |
| gemini-2.5-flash-lite (fallback actuel) | 0,10 $ / 1M tokens | 0,40 $ / 1M tokens |

L'app utilise déjà les deux modèles les moins chers de la gamme Gemini (pas de gemini-2.5-pro). Le fallback automatique vers flash-lite en cas d'erreur (429/503) est une bonne pratique déjà en place.

Note : Gemini 3.5 Flash est sorti depuis (modèle "actuel" chez Google mi-2026) — pas testé ici, à évaluer plus tard si vous voulez comparer qualité/prix, mais pas urgent : 2.5-flash reste supporté et fonctionne.

Si facturation activée : plafonds de sécurité intégrés par Google — Tier 1 (dès qu'un compte est lié) = 250$/mois max, au-delà le service se coupe automatiquement pour tout le compte jusqu'au mois suivant. Impossible de dépasser ce plafond par accident.

---

## 3. Quotas gratuits actuels (à vérifier dans votre tableau de bord)

Google ne publie plus de table statique — les quotas exacts sont désormais personnalisés et visibles uniquement sur [aistudio.google.com/rate-limit](https://aistudio.google.com/rate-limit). D'après les données agrégées les plus récentes (juillet 2026), à titre indicatif pour gemini-2.5-flash-lite en Free Tier : environ 15-30 requêtes/minute, ~1500 requêtes/jour, 1M tokens/minute. Le modèle flash (non-lite) a des limites plus basses.

**Point important : ces quotas sont au niveau du projet, pas par utilisateur.** Tous vos utilisateurs se partagent le même compteur journalier tant qu'ils passent par la clé serveur partagée. → Vérifiez vos chiffres réels dans AI Studio avant de vous fier à ces ordres de grandeur.

---

## 4. Ce qui a été corrigé aujourd'hui (v5.32)

**Rate limiting anti-abus** (`serve.js`) — avant ce fix, l'endpoint `/api/gemini` était totalement ouvert : n'importe qui trouvant l'URL Render pouvait l'appeler directement en dehors de l'appli (script, bot, scraper) et épuiser à lui seul tout le quota gratuit journalier partagé entre vos vrais utilisateurs. Ajouté : limite de 15 requêtes/minute et 300/jour par adresse IP, en mémoire, sans base de données. Un abus isolé ne peut plus faire tomber le service pour tout le monde.

**Priorité à la clé personnelle** (`serve.js`) — avant, même quand un utilisateur configurait sa propre clé Gemini gratuite dans Profil, le serveur ignorait systématiquement cette clé et utilisait toujours la clé partagée (`GEMINI_API_KEY` avait la priorité absolue). Résultat : la fonctionnalité "apporte ta propre clé" ne servait jamais à rien en production, alors qu'elle existe précisément pour soulager le quota partagé. Inversé : la clé perso passe maintenant en premier quand elle est configurée.

**Message d'erreur quota corrigé** (front-end) — le message affiché en cas de quota dépassé supposait toujours que c'était la clé personnelle de l'utilisateur qui était épuisée ("Ta clé Gemini a atteint sa limite... active la facturation sur aistudio.google.com"), alors qu'en usage normal (utilisateur sans clé perso) c'est la clé serveur partagée qui est en cause — et l'utilisateur n'a évidemment pas accès à ce compte AI Studio. Le message distingue maintenant les deux cas, et incite les utilisateurs actifs à configurer leur propre clé gratuite.

---

## 5. Plan de montée en charge (à activer dans cet ordre, seulement quand nécessaire)

**Palier 1 — maintenant :** Free Tier, clé serveur unique, rate limiting anti-abus (fait), message clair en cas de quota dépassé (fait), incitation BYOK pour les power users (fait). Coût : 0€, risque financier : 0€.

**Palier 2 — si le quota journalier partagé est régulièrement atteint :** créer 2-3 projets Google AI Studio distincts (chacun a son propre quota gratuit, les limites sont par projet donc ça multiplie la capacité gratuite totale sans dépenser un centime), et faire tourner `serve.js` en round-robin entre plusieurs `GEMINI_API_KEY`. Toujours 0€ de risque.

**Palier 3 — si la croissance est réelle et qu'un modèle de revenu existe (dons, version premium, partenariat) :** activer la facturation sur UN SEUL projet dédié, avec un plafond de dépense mensuel explicite fixé dans AI Studio (Tier 1 = 250$/mois par défaut, ajustable). Surveiller [aistudio.google.com/usage](https://aistudio.google.com/usage) chaque semaine les premiers mois.

**À ne jamais faire :** activer la facturation "au cas où" avant d'avoir une vraie raison — ça transforme un risque financier nul en risque réel, pour un bénéfice quasi nul tant que le quota gratuit suffit.

---

## 6. Ce qui reste à surveiller (pas encore fait, optionnel)

- `maxOutputTokens:8192` sur les réponses du chat principal (vs 2048 pour les autres appels IA de l'app) — généreux pour du texte de coaching, à réduire si un jour les quotas se tendent, mais attention : chaque réponse de Léo contient aussi un bloc JSON structuré ([FD]{...}) utilisé pour extraire vos données financières, donc une réduction trop agressive risquerait de le tronquer et de casser l'extraction automatique. À tester avant de changer.
- Pas de tableau de bord interne d'usage — pour l'instant, la seule source de vérité est le dashboard AI Studio de Google. Si le volume grossit, un compteur simple de messages/jour dans `serve.js` (déjà la bonne place, vu le rate limiter qui vient d'y être ajouté) donnerait une visibilité sans dépendre de Google.
