"""MHI IR Climate custom integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .ir_protocol import (
    DEFAULT_AUTO_CLEAN,
    DEFAULT_INSTALL_POSITION,
    DEFAULT_LED_BRIGHTNESS,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MHI IR Climate from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "climate_entity": None,
        "config": {**entry.data, **entry.options},
        "auto_clean": DEFAULT_AUTO_CLEAN,
        "install_position": DEFAULT_INSTALL_POSITION,
        "led_brightness": DEFAULT_LED_BRIGHTNESS,
    }

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload after options change."""

    await hass.config_entries.async_reload(entry.entry_id)
