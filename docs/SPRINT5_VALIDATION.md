# Sprint 5 Validation Checklist

## Upgrade
- [ ] HACS installs `v0.5.0-alpha-sprint5`
- [ ] Existing v0.4.3 configuration loads
- [ ] Dashboard Cockpit / Santé / Historique / Zendure still work
- [ ] New Automation view loads
- [ ] No unexpected log errors

## Automation
- [ ] Automation Engine switch turns simulated automation on/off
- [ ] Disabled state produces zero simulated output
- [ ] Grid import above target enters `discharge`
- [ ] Grid inside deadband enters `idle`
- [ ] Grid unavailable enters `safe_hold`
- [ ] No active battery enters `safe_hold`
- [ ] Fallback policy is respected
- [ ] Minimum hold timer prevents oscillating normal transitions
- [ ] Safety transition bypasses hold
- [ ] Cycle counter increments
- [ ] Last transition timestamp updates

## Safety
- [ ] Simulation Mode remains forced ON
- [ ] No real Zendure output limit is written
- [ ] Hyper and SolarFlow output-limit entities remain untouched
