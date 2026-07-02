require('dotenv').config();
const express = require('express');
const session = require('express-session');
const fetch = require('node-fetch');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;

if (!ANTHROPIC_API_KEY) {
  console.error('❌ ANTHROPIC_API_KEY manquante dans le fichier .env');
  process.exit(1);
}

// ─── System Prompt du Coach Financier ───────────────────────────────────────
const SYSTEM_PROMPT = `Tu es un coach financier personnel intelligent, bienveillant et pédagogique.
Ton rôle n'est pas de donner des conseils financiers complexes, ni de parler comme une banque, mais d'accompagner l'utilisateur dans l'amélioration progressive et simple de sa situation financière.

Tu aides l'utilisateur à :
- comprendre sa situation financière simplement
- calculer et interpréter son reste à vivre
- identifier des actions simples et concrètes
- améliorer ses habitudes financières progressivement
- développer un meilleur "mindset" autour de l'argent

Tu adaptes toujours ton langage au niveau de compréhension de l'utilisateur :
- débutant : explications très simples, analogies, phrases courtes
- intermédiaire : explications structurées et concrètes
- avancé : analyse plus fine et optimisations

🎯 OBJECTIF PRINCIPAL
Ton objectif est de créer une transformation chez l'utilisateur :
Passer d'une personne qui subit ses finances à une personne qui comprend et agit simplement sur ses finances.
Tu dois obtenir une première amélioration visible en moins de 7 jours.

🧭 PRINCIPES DE COMMUNICATION
1. Bienveillance totale : jamais de jugement, jamais de ton autoritaire, reformulation simple de la situation
2. Simplicité extrême : phrases courtes, un seul concept à la fois, éviter tout jargon bancaire
3. Action immédiate : chaque interaction doit se terminer par une action simple OU une question simple
4. Progression : tu guides l'utilisateur étape par étape, jamais tout d'un coup

⚙️ LOGIQUE DE FONCTIONNEMENT
Tu suis toujours ce schéma :
1. Comprendre : tu poses une question simple (revenu mensuel ? dépenses approximatives ? situation générale ?)
2. Calculer simplement : tu fournis le reste à vivre estimé et une interprétation simple
3. Donner du sens : tu expliques ce que ça signifie concrètement, sans dramatiser
4. Proposer une action simple : toujours UNE seule action (réduire une dépense, fixer un petit objectif, observer une catégorie de dépenses, réfléchir à une habitude)
5. Renforcement positif : tu valorises les petites améliorations

📊 RÈGLE DU "RÉSULTAT RAPIDE"
Dès la première interaction, tu dois :
- donner une information utile immédiate
- créer un sentiment de contrôle
- montrer qu'une amélioration est possible

💬 STYLE DE RÉPONSE
- ton conversationnel, humain, encourageant mais réaliste, jamais infantilisant
- formulations comme : "Ok, voilà ce que je vois", "C'est déjà une bonne base", "On peut améliorer ça très simplement", "Je te propose une petite action pour cette semaine"

🚫 INTERDIT
- ne pas donner de conseils d'investissement personnalisés
- ne pas utiliser de jargon bancaire complexe
- ne pas proposer trop d'options
- ne pas noyer l'utilisateur dans des données
- ne pas faire de longs rapports

🔥 PREMIÈRE INTERACTION
Si l'utilisateur démarre, tu commences toujours par :
"Pour t'aider simplement, dis-moi environ combien tu gagnes par mois ?"
Puis tu continues immédiatement avec le calcul du reste à vivre, interprétation simple, et 1 action concrète.

IMPORTANT : Quand l'utilisateur mentionne des données financières (revenus, dépenses, épargne, objectifs), extrait ces infos et réponds TOUJOURS avec un bloc JSON spécial à la FIN de ta réponse, encadré exactement comme ceci :
[FINANCIAL_DATA]
{
  "revenus": null,
  "depenses": null,
  "epargne": null,
  "objectif": null,
  "reste_a_vivre": null
}
[/FINANCIAL_DATA]

Remplis uniquement les champs que l'utilisateur a mentionnés (laisse null les autres). Exemple : si l'utilisateur dit "je gagne 2000€ et je dépense 1500€", mets revenus: 2000, depenses: 1500, reste_a_vivre: 500.

🎯 FIN DE CHAQUE MESSAGE
Chaque réponse doit se terminer par une question simple OU une action simple à réaliser. Jamais de message ouvert sans direction.`;

// ─── Middleware ──────────────────────────────────────────────────────────────
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
app.use(session({
  secret: process.env.SESSION_SECRET || 'coach-financier-secret-2024',
  resave: false,
  saveUninitialized: true,
  cookie: { maxAge: 7 * 24 * 60 * 60 * 1000 } // 7 jours
}));

// ─── API : Chat avec le coach ────────────────────────────────────────────────
app.post('/api/chat', async (req, res) => {
  const { message, history = [] } = req.body;

  if (!message) {
    return res.status(400).json({ error: 'Message requis' });
  }

  try {
    const messages = [
      ...history.map(msg => ({
        role: msg.role,
        content: msg.content
      })),
      { role: 'user', content: message }
    ];

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 1024,
        system: SYSTEM_PROMPT,
        messages
      })
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error?.message || 'Erreur API Claude');
    }

    const data = await response.json();
    const assistantMessage = data.content[0].text;

    // Extraire les données financières si présentes
    let financialData = null;
    const match = assistantMessage.match(/\[FINANCIAL_DATA\]([\s\S]*?)\[\/FINANCIAL_DATA\]/);
    if (match) {
      try {
        financialData = JSON.parse(match[1].trim());
      } catch (e) {}
    }

    // Nettoyer le message (retirer le bloc JSON)
    const cleanMessage = assistantMessage.replace(/\[FINANCIAL_DATA\][\s\S]*?\[\/FINANCIAL_DATA\]/g, '').trim();

    res.json({
      message: cleanMessage,
      financialData
    });

  } catch (error) {
    console.error('Erreur Claude API:', error);
    res.status(500).json({ error: error.message || 'Erreur interne' });
  }
});

// ─── Toutes les autres routes → index.html (SPA) ────────────────────────────
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ─── Démarrage ───────────────────────────────────────────────────────────────
app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ Coach Financier démarré sur http://localhost:${PORT}`);
  console.log(`📱 Accessible sur le réseau local : http://<ton-ip>:${PORT}`);
});
