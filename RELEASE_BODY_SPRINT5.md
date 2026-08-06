# Carpiquet EMS v0.5.8 — Sprint 5 Final

> **Every watt counts.**  
> Intelligent energy management for Zendure.  
> Designed with ❤️ in Normandy.  
> Engineered for reliability. Built for Home Assistant.

## Correctifs

- Réinitialisation complète des performances et énergies au début de chaque session.
- Correction de `performance_average_percent` afin qu’il reste dans une plage cohérente.
- Résumé énergétique reconstruit automatiquement après une interruption de Home Assistant.
- Statistiques de collecte ajoutées : durée mesurée, intervalles longs, intervalle maximal et dernier échantillon.
- Garde d’initialisation des SOC conservée.
- Finalisation atomique des rapports conservée.

## Sécurité

Cette version reste **100 % simulation**. Aucune commande réelle n’est envoyée aux appareils Zendure.

**Safety before performance. Always.**

Tag : `v0.5.8`  
Pré-release : Non  
Latest release : Oui
