# 🏴 Carpiquet EMS

> **Every watt counts.**

# 🤖 Sprint 5 — v0.5.3 Corrective

## Sessions
- ✅ ON/OFF du moteur sans reload Home Assistant
- ✅ Watchdog moteur ↔ session
- ✅ Nouvelle session propre à chaque redémarrage du moteur
- ✅ Clôture et sauvegarde JSON
- ✅ Préservation des sessions interrompues

## Modèle énergétique
La consommation maison est désormais reconstruite avec :

`Shelly + sorties maison Zendure - entrées AC Zendure`

- ✅ Hyper `grid_input_power`
- ✅ SolarFlow `grid_input_power`

## Rapports
- ✅ Sélection du rapport dans le Dashboard
- ✅ Bouton « Préparer le téléchargement »
- ✅ JSON exposé via `/local/carpiquet_ems_reports/`

## Interface
- ✅ État du moteur
- ✅ Plage de lissage
- ✅ Dans la plage de lissage

## Sécurité
**100 % simulation uniquement.**
Aucune commande réelle Zendure n'est envoyée.

Tag : `v0.5.3-alpha-sprint5`
Pré-release : **Oui**
