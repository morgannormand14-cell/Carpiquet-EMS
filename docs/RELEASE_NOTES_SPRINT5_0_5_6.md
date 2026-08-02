# Carpiquet EMS v0.5.6-alpha — Sprint 5

- Arrêt du moteur appliqué avant la finalisation du rapport.
- Blocage des échantillons tardifs pendant l'arrêt.
- Verrou thread-safe entre écriture et finalisation.
- `ended_at` positionné après le dernier échantillon accepté.
- Écriture atomique `.tmp` puis renommage du JSON final.
- Conservation du `.jsonl` en cas d'erreur.
- Nouveaux diagnostics de sauvegarde dans le Dashboard.
- Correction préventive du service d'installation du Dashboard.
- Simulation uniquement : aucune écriture réelle Zendure.
