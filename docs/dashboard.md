# Dashboard Carpiquet EMS

Copiez le dossier `dashboards` dans `/config/dashboards`, puis ajoutez ceci à `configuration.yaml` :

```yaml
lovelace:
  dashboards:
    carpiquet-ems:
      mode: yaml
      title: Carpiquet EMS
      icon: mdi:home-battery
      show_in_sidebar: true
      filename: dashboards/carpiquet_ems.yaml
```

Redémarrez ensuite Home Assistant.

Home Assistant conserve les anciens identifiants dans le registre des entités. Pour obtenir les noms `sensor.carpiquet_ems_*`, supprimez l'entrée Carpiquet EMS, redémarrez, puis recréez-la après la mise à jour.
