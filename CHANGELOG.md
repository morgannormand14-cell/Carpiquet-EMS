# Changelog

## 0.6.5-alpha.3.8 — Normandy Sprint 7 — Dashboard Lifecycle

- Ajout de l'enregistrement runtime autonome du Dashboard Lovelace Carpiquet EMS.
- Suppression de la dépendance fonctionnelle au bloc manuel `lovelace: dashboards:` après migration.
- Compatibilité avec l'ancien Dashboard YAML pendant la migration : aucun écrasement d'un panneau déjà déclaré par l'utilisateur.
- Conservation du fichier généré `dashboards/carpiquet_ems.yaml` comme source du Dashboard dynamique.
- Nettoyage du panneau runtime possédé par Carpiquet lors du déchargement et du fichier généré lors de la suppression de l'intégration.
- Ajout de la dépendance Home Assistant `lovelace` afin que le cycle de vie ne démarre qu'après l'initialisation Lovelace.
- Aucun changement du moteur EMS, de l'autorité, des écritures Zendure ou de la politique de Discovery.

## 0.6.5-alpha.3.7 — Normandy Sprint 7 — Step 2B

- Réconciliation manuelle de l'inventaire Zendure validée.
- **Synchroniser Carpiquet EMS** lance une découverte ponctuelle et compare le résultat à l'inventaire validé.
- Un inventaire identique est conservé et permet la régénération/réparation du Dashboard.
- Un inventaire différent reste en attente jusqu'à validation ou refus explicite.
- Aucune découverte matérielle périodique ou au démarrage.
- Invariants de sécurité conservés.
