# Sprint 3 Validation Checklist

## Upgrade

- [ ] HACS installs `v0.5.0-alpha-sprint5`
- [ ] Home Assistant restarts without integration errors
- [ ] Existing config entry loads successfully
- [ ] All expected entities remain available

## Config Flow

- [ ] Entity selectors are visible
- [ ] Invalid numeric limits are rejected
- [ ] Duplicate configuration is rejected
- [ ] Simulation warning is visible

## Options Flow

- [ ] Configure opens from Devices & services
- [ ] Source entities can be changed
- [ ] Numeric parameters can be changed
- [ ] Integration reloads after saving

## Dashboard installer

- [ ] `carpiquet_ems.install_dashboard` is available
- [ ] Service creates `/config/dashboards/carpiquet_ems.yaml`
- [ ] Existing file is protected when overwrite is false
- [ ] Overwrite works when explicitly enabled
- [ ] Persistent notification is displayed

## Dashboard

- [ ] Cockpit view loads
- [ ] Health view loads
- [ ] History view loads
- [ ] No `Entity not found` card is visible

## Safety

- [ ] Simulation switch cannot be turned off
- [ ] No Zendure output-limit entity is modified
- [ ] No real command is sent
- [ ] Home Assistant logs contain no unexpected errors
