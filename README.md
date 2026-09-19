# Carpiquet EMS

**Version packagée : 0.6.5-alpha.3.7 — Normandy Sprint 7 — Step 2B**

Carpiquet EMS est une intégration personnalisée Home Assistant qui pilote sa propre logique EMS à partir de la télémétrie et des capacités matérielles Zendure. Zendure-HA fournit la découverte, la topologie, les capacités et la télémétrie ; les décisions énergétiques restent sous l'autorité de Carpiquet EMS.

## Périmètre de cette alpha

Cette version ajoute la réconciliation manuelle de l'inventaire Zendure :

- découverte matérielle une fois pendant l'installation ;
- restauration au démarrage de l'inventaire explicitement validé, sans nouvelle découverte ;
- bouton **Synchroniser Carpiquet EMS** pour lancer une découverte ponctuelle ;
- comparaison entre l'inventaire validé et l'inventaire nouvellement détecté ;
- inventaire identique : conservation de l'inventaire et régénération/réparation du Dashboard ;
- inventaire différent : mise en attente des changements jusqu'à validation ou refus explicite dans **Configurer** ;
- une indisponibilité temporaire n'est pas utilisée comme preuve de retrait matériel ;
- aucune découverte matérielle périodique.

## Sécurité de cette version

Pendant Sprint 7 Step 2B :

- autorité moteur : `legacy_v0.6.4` ;
- moteur générique : `shadow_compare` ;
- autorité générique : désactivée ;
- écritures Zendure réelles : désactivées ;
- verrouillage des commandes : activé ;
- verrouillage de l'adaptateur de commandes : activé.

La couche de découverte/réconciliation ne donne aucune autorité de décision énergétique à Zendure Manager.

## Installation / mise à jour

Copier `custom_components/carpiquet_ems/` dans `/config/custom_components/carpiquet_ems/`, remplacer les fichiers de la version précédente puis redémarrer Home Assistant. Pour une mise à jour depuis alpha.3.6-r3, conserver l'entrée d'intégration existante.

Le Dashboard YAML généré est conservé dans le fonctionnement actuel. Dans cette alpha, l'enregistrement Lovelace automatique n'est pas encore activé : conserver la déclaration `lovelace:` déjà utilisée pour afficher le Dashboard dans la barre latérale.

## Validation attendue après redémarrage

Pour l'installation actuellement validée comme référence : `Discovery State = validated`, `Discovered Systems = 2`, `Discovered Batteries = 4`, `Mapper Ready = on`, `Mapper Systems = 2`, `Mapper Available = 2`. Les deux verrous de commande doivent rester `on` et les écritures réelles `off`.

## Contenu

Le ZIP d'installation contient uniquement le code nécessaire à cette version et quatre fichiers racine maintenus à jour : `README.md`, `CHANGELOG.md`, `PACKAGE_CONTENTS.md` et `LICENSE`. Les anciens Release Bodies, Build Validations et documentations de sprints devenues non applicables ne sont pas embarqués.
