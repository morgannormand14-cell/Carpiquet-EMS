# 🏴 Carpiquet EMS

> **Every watt counts.**

# ☀️ Sprint 5 — v0.5.4 Politique solaire & export EDF

## Correctifs
- ✅ Bouton de préparation des rapports corrigé
- ✅ Téléchargement répétable même si le dossier existe
- ✅ « Dans la plage de lissage » appliqué au moteur

## Nouvelle stratégie solaire
- ✅ Le PV des systèmes pleins alimente la maison en priorité
- ✅ Les systèmes non pleins réservent leur PV à la recharge
- ✅ Leur PV complète la maison uniquement si le PV des systèmes pleins est insuffisant
- ✅ La batterie ne décharge que lorsque le PV total ne couvre plus la maison

## Politique d'export
- ✅ Toutes les batteries pleines : export EDF simulé interdit
- ✅ Surplus non stockable : production simulée écrêtée
- ✅ Une batterie sous son SOC maximum : export réautorisé
- ✅ Stockage local et inter-systèmes toujours prioritaire

## Diagnostics
- ✅ Export EDF autorisé
- ✅ Motif de la politique d'export
- ✅ Systèmes pleins
- ✅ Production solaire écrêtée
- ✅ PV vers maison par système
- ✅ Batterie vers maison par système

## Sécurité
**100 % simulation uniquement.**
Aucune commande réelle Zendure n'est envoyée.

Tag : `v0.5.4-alpha-sprint5`
Pré-release : **Oui**
