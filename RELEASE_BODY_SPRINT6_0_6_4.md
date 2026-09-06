# Carpiquet EMS v0.6.4-alpha-sprint6 — Energy-Aware Discharge Engine

Cette pré-release introduit le nouveau moteur de décharge fondé sur l’énergie exploitable restante jusqu’au SOC minimum.

La répartition Hyper 2000 / SolarFlow 2400 Pro devient dynamique afin de faire converger les deux systèmes vers leur SOC minimum au même moment, tout en respectant les limites de 1 200 W et 2 400 W et en conservant jusqu’à 3 600 W de puissance combinée lorsque la demande l’exige.

La logique de charge, le Command Pipeline, le watchdog, la Safety State Machine, le mode Shadow et le Zendure Command Adapter restent protégés par l’architecture Sprint 6. Les écritures réelles Zendure restent HARD LOCKED dans cette pré-release.
