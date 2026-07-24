# 🏴 Carpiquet EMS

> **Every watt counts.**  
> **Intelligent energy management for Zendure.**  
> *Designed with ❤️ in Normandy.*

## 🚀 Sprint 3 — Onboarding

This pre-release improves the path from HACS installation to a working
Carpiquet EMS cockpit.

### ✨ Highlights

- Entity pickers in the configuration assistant
- Editable Options Flow after installation
- Guided Premium Dashboard installer
- Bundled dashboard YAML
- Improved French interface text
- Updated installation documentation
- Full validation checklist

### 🖥️ Dashboard installation

After restarting Home Assistant, run:

```yaml
action: carpiquet_ems.install_dashboard
data:
  overwrite: false
```

Then follow `docs/DASHBOARD_INSTALLATION.md`.

### 🛡️ Safety

This version remains **100% simulation-only**.

No command is sent to Zendure devices. Output-limit entities are never modified.

### 🏷️ Release

- Tag: `v0.3.0-alpha-sprint3`
- Pre-release: **Yes**
- Latest release: **No**
- Discussion category: **Announcements**

🏴 **Carpiquet EMS — Every watt counts.**
