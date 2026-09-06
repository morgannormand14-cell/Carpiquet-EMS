# Carpiquet EMS v0.6.4-alpha — Energy Balanced Discharge Engine

## Objectif
Préserver la puissance combinée Hyper 2000 + SolarFlow 2400 Pro jusqu’au SOC minimum en faisant converger les deux systèmes vers leur réserve au même moment.

## Changement moteur
- Répartition de décharge selon l’énergie exploitable restante au-dessus du SOC minimum.
- Capacités et SOC minimum propres à chaque système pris en compte.
- Redistribution automatique du reliquat lorsqu’un onduleur atteint sa limite.
- Puissance combinée maximale conservée : 1 200 W Hyper + 2 400 W SolarFlow = 3 600 W.
- Charge, sécurité, watchdog, Shadow et Zendure Command Adapter inchangés.
- Écritures réelles toujours verrouillées.

## Validation
Tests unitaires ajoutés pour le ratio énergétique, la correction d’un déséquilibre de SOC, la puissance combinée 3,6 kW et l’arrêt individuel au SOC minimum.
