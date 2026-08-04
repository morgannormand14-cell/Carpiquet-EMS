# v0.5.7 — Garde d'initialisation du moteur

Cette version finale du Sprint 5 empêche une session de démarrer avec des
valeurs de SOC nulles ou indisponibles.

## Démarrage

1. L'utilisateur active le moteur.
2. Carpiquet EMS passe en `Initialisation du moteur`.
3. Le système attend jusqu'à 30 secondes que les SOC et entités essentielles
   soient disponibles.
4. Si les données sont valides, le snapshot réel est utilisé pour initialiser
   les batteries virtuelles et la session démarre.
5. Si les données restent invalides, le moteur revient sur OFF et passe en
   `Maintien de sécurité`.

## Diagnostics

- Initialisation du moteur
- Données initiales valides
- Erreur d'initialisation

Cette version conserve la finalisation atomique des rapports de la v0.5.6.
