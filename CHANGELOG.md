# Changelog

## 0.6.5-alpha.3.7 — Normandy Sprint 7 — Step 2B

- Ajout de la réconciliation manuelle de l'inventaire Zendure.
- **Synchroniser Carpiquet EMS** lance une découverte ponctuelle et compare le résultat à l'inventaire validé.
- Un inventaire identique est conservé et permet la régénération/réparation du Dashboard.
- Un inventaire différent reste en attente et ne remplace pas l'inventaire runtime tant que l'utilisateur ne l'a pas explicitement validé.
- Ajout des actions de configuration pour valider ou refuser les changements détectés.
- Une indisponibilité temporaire n'est pas interprétée comme un retrait matériel.
- Conservation de la politique : découverte à l'installation ou sur synchronisation manuelle uniquement ; aucune découverte périodique ou au démarrage.
- Conservation des invariants de sécurité : moteur legacy autoritaire, moteur générique en `shadow_compare`, écritures Zendure réelles désactivées et verrous de commande activés.
- Le cycle de vie Lovelace automatique n'est pas encore activé ; le fonctionnement Dashboard existant est conservé.
- Packaging épuré : seuls le code nécessaire et les quatre documents racine à jour sont livrés.
