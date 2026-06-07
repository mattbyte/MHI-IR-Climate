"""Switch entities for MHI IR Climate."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .ir_protocol import DEFAULT_AUTO_CLEAN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""

    runtime_data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MHIIRAutoCleanSwitch(entry, runtime_data)])


class MHIIRAutoCleanSwitch(SwitchEntity, RestoreEntity):
    """Auto clean configuration switch."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_name = "Auto clean"

    def __init__(self, entry: ConfigEntry, runtime_data: dict[str, Any]) -> None:
        """Initialize the switch."""

        self._runtime_data = runtime_data
        self._attr_is_on = bool(runtime_data.get("auto_clean", DEFAULT_AUTO_CLEAN))
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_auto_clean"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }

    async def async_added_to_hass(self) -> None:
        """Restore the auto clean setting."""

        await super().async_added_to_hass()

        previous_state = await self.async_get_last_state()
        if previous_state is not None:
            self._attr_is_on = previous_state.state == STATE_ON

        self._runtime_data["auto_clean"] = self._attr_is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable auto clean."""

        await self._async_set_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable auto clean."""

        await self._async_set_enabled(False)

    async def _async_set_enabled(self, enabled: bool) -> None:
        """Set auto clean and send any required IR command."""

        self._attr_is_on = enabled
        self._runtime_data["auto_clean"] = enabled
        self.async_write_ha_state()

        climate_entity = self._runtime_data.get("climate_entity")
        if climate_entity is not None:
            await climate_entity.async_auto_clean_setting_changed(enabled)
