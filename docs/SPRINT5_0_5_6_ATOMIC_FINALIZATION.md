# v0.5.6 — Finalisation atomique des sessions

La v0.5.6 sécurise l'arrêt du moteur de simulation.

## Ordre d'arrêt

1. Le moteur passe immédiatement sur OFF.
2. Les nouveaux échantillons sont refusés.
3. Le cycle éventuellement déjà engagé se termine.
4. Le recorder verrouille le fichier temporaire.
5. `ended_at` est enregistré après le dernier échantillon accepté.
6. Le rapport est écrit dans un fichier `.tmp`.
7. Le fichier temporaire est renommé atomiquement en `SIM-....json`.
8. Le `.jsonl` est supprimé uniquement après succès.

En cas d'échec, le `.jsonl` est conservé pour récupération automatique au
prochain démarrage de Home Assistant.

## Diagnostics

- État de l'enregistrement
- Finalisation en cours
- Erreur de sauvegarde
- Dernière fin de session
