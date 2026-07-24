from __future__ import annotations

from pathlib import Path
import shutil

from homeassistant.core import HomeAssistant

from .const import DASHBOARD_FILENAME, DASHBOARD_RELATIVE_PATH


def install_dashboard_file(hass: HomeAssistant, overwrite: bool = False) -> Path:
    source = Path(__file__).parent / "dashboard" / DASHBOARD_FILENAME
    target = Path(hass.config.path(DASHBOARD_RELATIVE_PATH))
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and not overwrite:
        raise FileExistsError(str(target))

    shutil.copyfile(source, target)
    return target
