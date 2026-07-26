# Sprint 4 v0.4.1 Validation Checklist

## Installation
- [ ] Config Flow opens
- [ ] 8 dynamic Zendure entity selectors are visible
- [ ] Live values seed initial fallbacks
- [ ] Hyper pack count is detected
- [ ] SolarFlow pack count is detected
- [ ] Battery type + serial step appears
- [ ] AB2000X / I2400 / AB3000L mappings validate

## Runtime
- [ ] Data Mode = LIVE with all 8 sources available
- [ ] Changing capacity updates the value and persistent fallback
- [ ] Changing max power updates the value and persistent fallback
- [ ] Changing min/max SOC updates the value and persistent fallback
- [ ] Making one source unavailable changes Data Mode to FALLBACK ACTIF
- [ ] Last valid fallback is used
- [ ] Returning the source restores LIVE

## Cockpit
- [ ] Batteries actives / total shown
- [ ] Total capacity shown
- [ ] Weighted average SOC shown
- [ ] Available power shown
- [ ] Health shown
- [ ] LIVE / FALLBACK ACTIF shown

## Zendure view
- [ ] Hyper system card loads
- [ ] SolarFlow system card loads
- [ ] Generated battery blocks match topology
- [ ] No Entity not found

## Safety
- [ ] Simulation mode remains enabled
- [ ] `number.hyper_2000_output_limit` is never written
- [ ] `number.solarflow_2400_pro_output_limit` is never written
- [ ] No unexpected Home Assistant errors
