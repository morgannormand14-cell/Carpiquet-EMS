# v0.5.4 — Politique solaire et export EDF

## Priorité des systèmes pleins

Lorsqu'un système a atteint son SOC maximum, sa production solaire alimente la
maison en priorité.

Le solaire d'un système dont la batterie peut encore charger est conservé pour
sa batterie tant que la production des systèmes pleins suffit à la maison.

Ordre de décision :

1. PV des systèmes pleins vers la maison ;
2. si nécessaire, PV des systèmes non pleins vers la maison ;
3. si le PV total est insuffisant, décharge batterie ;
4. surplus PV vers la batterie locale ;
5. surplus restant vers l'autre système ;
6. export EDF ou écrêtage selon l'état global des batteries.

## Interdiction d'export quand tout est plein

Lorsque toutes les batteries disponibles ont atteint leur SOC maximum :

- l'export EDF simulé est interdit ;
- le surplus impossible à stocker est comptabilisé comme production écrêtée ;
- le réseau simulé ne devient pas négatif à cause de ce surplus.

Dès qu'une batterie repasse sous son SOC maximum :

- l'export EDF est réautorisé ;
- le stockage local et inter-systèmes reste prioritaire ;
- seul le reliquat impossible à stocker est exporté.

## Diagnostics

Nouvelles entités :

- export EDF autorisé ;
- motif de la politique d'export ;
- nombre de systèmes pleins ;
- production solaire écrêtée ;
- PV Hyper/SolarFlow vers maison ;
- décharge batterie Hyper/SolarFlow vers maison.
