from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, VERSION

PANEL_URL_PATH = "spizarka"
PANEL_TITLE = "Spiżarka"
PANEL_ICON = "mdi:food-apple-outline"
PANEL_ELEMENT = "spizarka-panel"
STATIC_URL = "/spizarka_static"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register Spiżarka frontend panel."""
    marker = f"{DOMAIN}_frontend_registered"
    if not hass.data.get(marker):
        frontend_dir = Path(__file__).parent / "frontend"
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(frontend_dir), cache_headers=False)]
        )
        hass.data[marker] = True

    # Ensure reload/update is idempotent.
    if PANEL_URL_PATH in hass.data.get("frontend_panels", {}):
        frontend.async_remove_panel(hass, PANEL_URL_PATH, warn_if_unknown=False)

    await panel_custom.async_register_panel(
        hass,
        webcomponent_name=PANEL_ELEMENT,
        frontend_url_path=PANEL_URL_PATH,
        module_url=f"{STATIC_URL}/spizarka-panel.js?v={VERSION}",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        require_admin=False,
        config={"version": VERSION},
        config_panel_domain=DOMAIN,
    )


def async_unregister_panel(hass: HomeAssistant) -> None:
    """Unregister Spiżarka frontend panel."""
    frontend.async_remove_panel(hass, PANEL_URL_PATH, warn_if_unknown=False)
