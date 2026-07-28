# v0.5.2 — Sessions de simulation

Le passage `Moteur d'automatisation OFF → ON` démarre désormais une nouvelle session indépendante.

## ON
- remet à zéro le jumeau numérique ;
- relit les données réelles courantes ;
- réinitialise cycles et indices de performance ;
- crée un identifiant `SIM-YYYYMMDD-HHMMSS` ;
- enregistre chaque cycle dans la session.

## OFF
- clôture la session ;
- calcule le résumé ;
- écrit un fichier JSON unique dans :
  `/config/carpiquet_ems/simulations/`

Le fichier contient :
- métadonnées ;
- état initial ;
- configuration ;
- échantillons cycle par cycle ;
- résumé final.

Ces fichiers peuvent être fournis pour une analyse ultérieure.
