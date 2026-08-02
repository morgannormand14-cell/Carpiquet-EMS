# 🏴 Carpiquet EMS

> **Every watt counts.**

# Sprint 5 — v0.5.6 Finalisation atomique

## Correctif principal
- ✅ Le moteur passe immédiatement sur OFF
- ✅ Aucun nouvel échantillon n'est accepté pendant la finalisation
- ✅ `ended_at` correspond au dernier cycle réellement enregistré
- ✅ Rapport écrit de manière atomique
- ✅ Fichier de secours conservé en cas d'échec
- ✅ Récupération automatique après interruption Home Assistant

## Diagnostics
- État de l'enregistrement
- Finalisation en cours
- Erreur de sauvegarde
- Dernière fin de session

## Sécurité
**100 % simulation uniquement.**
Aucune commande réelle Zendure n'est envoyée.

Tag : `v0.5.6-alpha-sprint5`
Pré-release : **Oui**
