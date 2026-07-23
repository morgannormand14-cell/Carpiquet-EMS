# Algorithm v0.1.1-alpha

1. Read Shelly grid power.
2. Positive means EDF import; negative means EDF export.
3. Apply target and deadband.
4. Positive import above deadband becomes requested discharge.
5. A battery at or below minimum SOC is protected.
6. Remaining requested power is allocated according to usable energy above minimum SOC.
7. Each inverter maximum is respected.
8. Simulation outputs include theoretical battery power and simulated grid power.
9. No Zendure output-limit entity is written.

Known limitation: this is a proportional baseline and does not yet guarantee identical time-to-minimum-SOC. That is planned for the next balancing algorithm.
