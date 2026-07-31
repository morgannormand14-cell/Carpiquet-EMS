# v0.5.5 — Jumeau numérique dynamique

La v0.5.5 remplace le comportement algébrique parfait par une simulation dynamique.

## Dynamique
- la plage de lissage est appliquée au jumeau numérique ;
- la rampe configurée limite les variations de charge et de décharge entre deux cycles ;
- les consignes précédentes sont conservées ;
- le réseau simulé est calculé après application des contraintes ;
- la puissance de charge/décharge est limitée par l'énergie réellement disponible jusqu'aux SOC min/max.

## Performance
Le score reste à 100 % dans la plage de lissage puis décroît progressivement. La session conserve aussi les moyennes et les bilans énergétiques cumulés.

## Reconstruction maison
La valeur brute est conservée pour diagnostic, mais une valeur négative issue du décalage temporel entre capteurs est bornée à 0 W pour le calcul énergétique.

## Rapports
Le bouton de préparation du rapport utilise l'API Home Assistant du composant `persistent_notification`. La préparation du fichier reste indépendante de la notification.
