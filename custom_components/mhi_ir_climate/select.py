"""Select entities for MHI IR Climate."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .ir_protocol import (
    DEFAULT_LED_BRIGHTNESS,
    LED_BRIGHTNESS_MODES,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities."""

    runtime_data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MHIIRPowerLedSelect(entry, runtime_data)])


class MHIIRPowerLedSelect(SelectEntity, RestoreEntity):
    """Power LED brightness select."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_name = "Power LED brightness"
    _attr_options = list(LED_BRIGHTNESS_MODES)

    def __init__(self, entry: ConfigEntry, runtime_data: dict[str, Any]) -> None:
        """Initialize the select."""

        self._entry = entry
        self._runtime_data = runtime_data
        self._attr_current_option = runtime_data.get(
            "led_brightness",
            DEFAULT_LED_BRIGHTNESS,
        )
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_power_led"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }

    async def async_added_to_hass(self) -> None:
        """Restore the selected LED brightness."""

        await super().async_added_to_hass()

        previous_state = await self.async_get_last_state()
        if previous_state is not None and previous_state.state in LED_BRIGHTNESS_MODES:
            self._attr_current_option = previous_state.state

        self._runtime_data["led_brightness"] = self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        """Select a new LED brightness."""

        if option not in LED_BRIGHTNESS_MODES:
            raise HomeAssistantError(f"Unsupported LED brightness: {option}")

        self._attr_current_option = option
        self._runtime_data["led_brightness"] = option
        self.async_write_ha_state()

        climate_entity = self._runtime_data.get("climate_entity")
        if climate_entity is not None:
            await climate_entity.async_send_current_state_if_on()
