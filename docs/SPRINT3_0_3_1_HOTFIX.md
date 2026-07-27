# Sprint 3 Hotfix — v0.5.1-alpha-sprint5

## Correctif

La première pré-release Sprint 3 pouvait empêcher l'ouverture du Config Flow avec :

`cannot import name 'CONF_OVERWRITE' from 'homeassistant.const'`

Le correctif définit maintenant cette clé localement dans Carpiquet EMS :

```python
CONF_OVERWRITE = "overwrite"
```

Le composant n'importe plus ce symbole depuis `homeassistant.const`.

## Validation

- [ ] Le Config Flow s'ouvre sans erreur
- [ ] Les sélecteurs d'entités fonctionnent
- [ ] L'Options Flow fonctionne
- [ ] Les entités Carpiquet EMS sont disponibles
- [ ] `carpiquet_ems.install_dashboard` est disponible
- [ ] Le Premium Dashboard fonctionne
- [ ] Aucun pilotage réel Zendure
- [ ] Aucun ImportError Carpiquet EMS dans les journaux

## Release

`v0.5.1-alpha-sprint5`
