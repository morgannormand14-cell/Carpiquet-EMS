# RFC-0005 — Moteur d'automatisation et jumeau numérique

## Objectif
Valider l'algorithme EMS contre l'installation réelle avant tout pilotage matériel.

## Reconstitution maison
`maison = Shelly + sortie Hyper + sortie SolarFlow`

## Priorités
1. alimenter la maison ;
2. stocker le surplus PV localement ;
3. exporter vers le bus AC le surplus local impossible à stocker ;
4. redistribuer ce surplus vers l'autre batterie ;
5. injecter seulement le reliquat impossible à stocker ;
6. en déficit, décharger en respectant SOC minimum et limites.

## Sécurité
Aucune commande réelle Zendure n'est envoyée.
