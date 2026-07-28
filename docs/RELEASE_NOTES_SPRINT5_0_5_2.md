# Carpiquet EMS v0.5.2-alpha — Sprint 5 corrective

- IDs techniques stabilisés pour les nouvelles entités.
- Dashboard réaligné avec les IDs Home Assistant.
- Capteurs de santé et sécurité corrigés.
- Valeurs visibles francisées : Sain, Attention, Critique, Direct, Secours actif, Jamais.
- OFF → ON du moteur démarre une nouvelle session de simulation.
- OFF clôture et sauvegarde la session précédente.
- Export JSON unique par session dans `/config/carpiquet_ems/simulations/`.
- Compteurs, jumeau numérique et performance remis à zéro au début d'une session.
- Simulation uniquement conservée.
