"""Button entities for MHI IR Climate."""

from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""

    runtime_data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MHIIRForceSendButton(entry, runtime_data)])


class MHIIRForceSendButton(ButtonEntity):
    """Force-send the current climate IR command."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_name = "Force send IR command"

    def __init__(self, entry: ConfigEntry, runtime_data: dict[str, Any]) -> None:
        """Initialize the button."""

        self._runtime_data = runtime_data
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_force_send"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }

    async def async_press(self) -> None:
        """Force-send the current IR command."""

        climate_entity = self._runtime_data.get("climate_entity")
        if climate_entity is None:
            raise HomeAssistantError("MHI IR climate entity is not ready")

        await climate_entity.async_force_send_current_state()
