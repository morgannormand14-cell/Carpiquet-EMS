# v0.5.3-alpha — Sprint 5 corrective

## Session recorder
Le switch du moteur est désormais un état runtime. Il ne modifie plus la Config Entry et ne déclenche plus de reload Home Assistant.

Invariant :
- moteur ON + aucune session → session créée automatiquement ;
- moteur OFF + session active → session clôturée automatiquement.

Un reload/redémarrage clôture la session avec `termination = home_assistant_reload` ou récupère un fichier temporaire interrompu au prochain démarrage.

## Consommation maison reconstituée
Nouvelle formule :

`Shelly + output_home Hyper + output_home SolarFlow - grid_input Hyper - grid_input SolarFlow`

Sources ajoutées :
- `sensor.hyper_2000_grid_input_power`
- `sensor.solarflow_2400_pro_grid_input_power`

## Rapports
Le dashboard permet de sélectionner un rapport JSON puis de préparer son téléchargement.
Le fichier est copié dans `/config/www/carpiquet_ems_reports/` et exposé sous `/local/carpiquet_ems_reports/...`.

## Vocabulaire
- État automation → État du moteur
- Bande morte → Plage de lissage
- Dans la bande morte → Dans la plage de lissage
