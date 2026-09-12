# Carpiquet EMS v0.6.5-alpha.3.2 — Normandy Sprint 6 — Release Sync Hotfix

Cette version corrige la chaîne de publication GitHub/HACS de la v0.6.5-alpha.3.1.

## Corrections

- Synchronisation du code publié avec le package d’installation.
- Version runtime et manifest alignée sur `0.6.5-alpha.3.2`.
- Conservation du correctif `desired_deficit` du Generic Energy Engine.
- Conservation de la reconstruction explicite de la demande de décharge.
- Conservation de la synchronisation de l’état de ramping précédent entre Legacy et Generic Engine.
- Nettoyage des artefacts de build/cache Python dans le package.
- Test de version du manifest aligné sur la release.

## Architecture

- Legacy Energy-Aware v0.6.4 : autorité EMS.
- Generic Energy Engine : `SHADOW_COMPARE`.
- Architecture générique : 1 à 5 systèmes.
- Entity Mapper / Control Profiles : inchangés.
- Safety Pipeline : inchangé.
- Real Zendure writes : **LOCKED**.

## Objectif de validation

Après installation via HACS et redémarrage complet de Home Assistant, une nouvelle session doit enregistrer :

- `version: 0.6.5-alpha.3.2`
- `generic_energy_engine`
- `generic_engine_parity_exact`

Cette version remplace alpha.3.1 pour la validation Dual Engine Shadow du Sprint 6.
