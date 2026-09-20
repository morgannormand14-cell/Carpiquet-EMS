# Carpiquet EMS

**Version packagée : 0.6.5-alpha.3.8 — Normandy Sprint 7 — Dashboard Lifecycle**

Carpiquet EMS est une intégration personnalisée Home Assistant qui pilote sa propre logique EMS à partir de la télémétrie et des capacités matérielles Zendure. Zendure-HA fournit la découverte, la topologie, les capacités et la télémétrie ; les décisions énergétiques restent sous l'autorité de Carpiquet EMS.

## Périmètre de cette alpha

Cette version conserve la réconciliation d'inventaire validée en alpha.3.7 et ajoute le cycle de vie autonome du Dashboard :

- génération/réparation du fichier `/config/dashboards/carpiquet_ems.yaml` au démarrage validé ;
- enregistrement runtime du Dashboard Lovelace `carpiquet-ems-dynamic` dans la barre latérale sans déclaration manuelle dans `configuration.yaml` ;
- compatibilité de migration : si l'ancien Dashboard est encore déclaré manuellement, Carpiquet le détecte et ne le remplace pas ;
- après retrait du bloc `lovelace:` historique et redémarrage, Carpiquet enregistre lui-même son Dashboard ;
- **Synchroniser Carpiquet EMS** continue de régénérer le Dashboard uniquement lorsque l'inventaire est identique ;
- déchargement : Carpiquet ne retire que le panneau runtime qu'il a lui-même enregistré ;
- suppression de l'intégration : nettoyage du panneau Carpiquet qu'elle possède et du fichier Dashboard généré ;
- aucun changement d'autorité EMS ou de politique de découverte matérielle.

## Migration depuis alpha.3.7

Mettre à jour vers alpha.3.8. Le premier démarrage reste compatible avec l'ancien bloc `lovelace:`. Après validation du démarrage alpha.3.8, supprimer de `configuration.yaml` le bloc manuel `carpiquet-ems-dynamic`, puis redémarrer Home Assistant. Carpiquet EMS doit alors recréer automatiquement l'entrée de barre latérale avec le même chemin URL.

## Sécurité de cette version

Les invariants restent inchangés : autorité moteur `legacy_v0.6.4`, moteur générique `shadow_compare`, autorité générique désactivée, écritures Zendure réelles désactivées, verrouillage des commandes et de l'adaptateur activé.

La découverte matérielle reste limitée à l'installation et à **Synchroniser Carpiquet EMS**. Aucune découverte périodique ou au démarrage n'est ajoutée.

## Validation attendue

Référence actuelle : `Discovery State = validated`, `Discovered Systems = 2`, `Discovered Batteries = 4`, `Mapper Ready = on`, `Mapper Systems = 2`, `Mapper Available = 2`. Après retrait du bloc Lovelace manuel et redémarrage, **Carpiquet EMS Dynamic** doit rester présent dans la barre latérale et ouvrir le Dashboard généré.

## Contenu

Le package conserve uniquement le code nécessaire et les quatre documents racine maintenus à jour : `README.md`, `CHANGELOG.md`, `PACKAGE_CONTENTS.md` et `LICENSE`.
