# 🏴 Carpiquet EMS

> **Every watt counts.**

# 🤖 Sprint 5 — v0.5.5 Jumeau numérique dynamique

## Correctifs
- ✅ Préparation des rapports compatible Home Assistant
- ✅ Notification découplée de la génération du fichier
- ✅ Plage de lissage appliquée au jumeau numérique

## Simulation dynamique
- ✅ Mémoire des consignes précédentes
- ✅ Rampe de puissance appliquée par cycle
- ✅ SOC min/max et énergie disponible respectés
- ✅ Réseau simulé calculé après les contraintes
- ✅ La simulation n'est plus forcée mathématiquement à 0 W

## Performance
- ✅ Score progressif
- ✅ Moyenne Carpiquet sur la session
- ✅ Moyenne de référence Zendure
- ✅ Import/export réel cumulés
- ✅ Import/export simulés cumulés
- ✅ Énergie PV stockée
- ✅ Énergie PV écrêtée

## Stratégie solaire v0.5.4 conservée
- ✅ PV des systèmes pleins prioritaire vers la maison
- ✅ PV des systèmes non pleins réservé autant que possible à leur recharge
- ✅ Export EDF simulé interdit lorsque toutes les batteries sont pleines
- ✅ Export réautorisé dès qu'une batterie repasse sous son SOC maximum

## Sécurité
**100 % simulation uniquement.** Aucune commande réelle Zendure n'est envoyée.

Tag : `v0.5.5-alpha-sprint5`
Pré-release : **Oui**
