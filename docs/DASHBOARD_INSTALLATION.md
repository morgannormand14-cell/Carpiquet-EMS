# Premium Dashboard Installation

## Recommended procedure

1. Restart Home Assistant after updating Carpiquet EMS.
2. Open **Developer Tools → Actions**.
3. Run:

```yaml
action: carpiquet_ems.install_dashboard
data:
  overwrite: false
```

The file is copied to:

```text
/config/dashboards/carpiquet_ems.yaml
```

## Add it to Home Assistant

### Storage-mode method

Create a new dashboard from **Settings → Dashboards**, open its raw
configuration editor, and paste the content of the installed YAML file.

### YAML-mode method

Add the following manually to `configuration.yaml`:

```yaml
lovelace:
  mode: storage
  dashboards:
    carpiquet-ems:
      mode: yaml
      title: Carpiquet EMS
      icon: mdi:home-lightning-bolt
      show_in_sidebar: true
      filename: dashboards/carpiquet_ems.yaml
```

Restart Home Assistant after editing `configuration.yaml`.

## Safety

The installer only copies a YAML file. It never sends commands to Zendure
devices and never edits `configuration.yaml`.
