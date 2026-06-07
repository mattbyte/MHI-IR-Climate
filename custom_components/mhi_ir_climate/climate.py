"""Climate platform for MHI IR Climate."""

from __future__ import annotations

from typing import Any, cast

from homeassistant.components import infrared
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import (
    ATTR_CURRENT_HUMIDITY,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_HVAC_MODE,
    ATTR_SWING_HORIZONTAL_MODE,
    ATTR_SWING_MODE,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_NAME,
    PRECISION_TENTHS,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    ATTR_INFRARED_EMITTER_ENTITY_ID,
    ATTR_LAST_ON_HVAC_MODE,
    ATTR_LAST_SWING_HORIZONTAL_MODE,
    ATTR_LAST_SWING_MODE,
    ATTR_MODEL,
    CONF_BASE_FRAME_HEX,
    CONF_EMITTER_ENTITY_ID,
    CONF_HUMIDITY_SENSOR,
    CONF_MODEL,
    CONF_TEMPERATURE_SENSOR,
    DOMAIN,
    MODEL_LABELS,
)
from .ir_protocol import SWING_HORIZONTAL_MODES, SWING_MODES, build_mhi_ir_command

DEFAULT_TARGET_TEMPERATURE = 24
MIN_TARGET_TEMPERATURE = 18
MAX_TARGET_TEMPERATURE = 30
SUPPORTED_HVAC_MODES = (HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT)
ON_HVAC_MODES = (HVACMode.COOL, HVACMode.HEAT)
SWING_3D_AUTO = "3D Auto"
SWING_STOP = "Stop"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the climate entity for a config entry."""

    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MHIIRClimateEntity(hass, entry, data)])


class MHIIRClimateEntity(ClimateEntity, RestoreEntity):
    """Optimistic MHI climate entity backed by an infrared emitter."""

    _attr_has_entity_name = False
    _attr_max_temp = MAX_TARGET_TEMPERATURE
    _attr_min_temp = MIN_TARGET_TEMPERATURE
    _attr_precision = PRECISION_TENTHS
    _attr_should_poll = False
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.SWING_HORIZONTAL_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_target_temperature_step = 1
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        data: dict[str, Any],
    ) -> None:
        """Initialize the climate entity."""

        self.hass = hass
        self._entry = entry
        self._emitter_entity_id = data[CONF_EMITTER_ENTITY_ID]
        self._temperature_sensor_entity_id = _optional_entity_id(
            data.get(CONF_TEMPERATURE_SENSOR)
        )
        self._humidity_sensor_entity_id = _optional_entity_id(
            data.get(CONF_HUMIDITY_SENSOR)
        )
        self._base_frame_hex = data[CONF_BASE_FRAME_HEX]
        self._model = data[CONF_MODEL]
        self._model_label = MODEL_LABELS.get(self._model, self._model)
        self._name = data[CONF_NAME]
        self._last_on_hvac_mode = HVACMode.COOL
        self._last_swing_mode: str | None = None
        self._last_swing_horizontal_mode: str | None = None

        self._attr_name = self._name
        self._attr_unique_id = entry.unique_id or entry.entry_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "manufacturer": "Mitsubishi Heavy Industries",
            "model": self._model_label,
            "name": self._name,
        }
        self._attr_hvac_modes = list(SUPPORTED_HVAC_MODES)
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_swing_modes = list(SWING_MODES)
        self._attr_swing_mode = SWING_3D_AUTO
        self._attr_swing_horizontal_modes = list(SWING_HORIZONTAL_MODES)
        self._attr_swing_horizontal_mode = SWING_3D_AUTO
        self._attr_target_temperature = DEFAULT_TARGET_TEMPERATURE
        self._attr_current_temperature = None
        self._attr_current_humidity = None

    async def async_added_to_hass(self) -> None:
        """Restore state and subscribe to sensor/emitter changes."""

        await super().async_added_to_hass()
        await self._async_restore_previous_state()

        tracked_entity_ids = [self._emitter_entity_id]
        if self._temperature_sensor_entity_id:
            tracked_entity_ids.append(self._temperature_sensor_entity_id)
        if self._humidity_sensor_entity_id:
            tracked_entity_ids.append(self._humidity_sensor_entity_id)

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                tracked_entity_ids,
                self._async_tracked_state_changed,
            )
        )

    @property
    def available(self) -> bool:
        """Return whether the configured infrared emitter is available."""

        state = self.hass.states.get(self._emitter_entity_id)
        return state is not None and state.state != STATE_UNAVAILABLE

    @property
    def current_temperature(self) -> float | None:
        """Return the current room temperature."""

        return self._read_sensor_float(
            self._temperature_sensor_entity_id,
            cast(float | None, self._attr_current_temperature),
        )

    @property
    def current_humidity(self) -> int | None:
        """Return the current room humidity."""

        humidity = self._read_sensor_float(
            self._humidity_sensor_entity_id,
            cast(float | None, self._attr_current_humidity),
        )
        return None if humidity is None else round(humidity)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return integration-specific state attributes."""

        return {
            ATTR_INFRARED_EMITTER_ENTITY_ID: self._emitter_entity_id,
            ATTR_LAST_ON_HVAC_MODE: self._last_on_hvac_mode.value,
            ATTR_LAST_SWING_MODE: self._last_swing_mode,
            ATTR_LAST_SWING_HORIZONTAL_MODE: self._last_swing_horizontal_mode,
            ATTR_MODEL: self._model_label,
        }

    async def async_set_hvac_mode(self, hvac_mode: HVACMode | str) -> None:
        """Set HVAC mode and send a matching IR command."""

        mode = _coerce_hvac_mode(hvac_mode)
        if mode not in SUPPORTED_HVAC_MODES:
            raise HomeAssistantError(f"Unsupported HVAC mode: {hvac_mode}")

        self._attr_hvac_mode = mode
        if mode in ON_HVAC_MODES:
            self._last_on_hvac_mode = mode

        self.async_write_ha_state()
        await self._async_send_current_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature and send an IR command if the unit is on."""

        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            self._attr_target_temperature = _clamp_temperature(temperature)

        if hvac_mode := kwargs.get(ATTR_HVAC_MODE):
            await self.async_set_hvac_mode(hvac_mode)
            return

        self.async_write_ha_state()
        if self._attr_hvac_mode != HVACMode.OFF:
            await self._async_send_current_state()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set vertical swing mode and send an IR command if the unit is on."""

        if swing_mode not in self._attr_swing_modes:
            raise HomeAssistantError(f"Unsupported swing mode: {swing_mode}")

        self._set_vertical_swing_mode(swing_mode)
        self.async_write_ha_state()
        if self._attr_hvac_mode != HVACMode.OFF:
            await self._async_send_current_state()

    async def async_set_swing_horizontal_mode(
        self,
        swing_horizontal_mode: str,
    ) -> None:
        """Set horizontal swing mode and send an IR command if the unit is on."""

        if swing_horizontal_mode not in self._attr_swing_horizontal_modes:
            raise HomeAssistantError(
                f"Unsupported horizontal swing mode: {swing_horizontal_mode}"
            )

        self._set_horizontal_swing_mode(swing_horizontal_mode)
        self.async_write_ha_state()
        if self._attr_hvac_mode != HVACMode.OFF:
            await self._async_send_current_state()

    async def async_turn_on(self) -> None:
        """Turn on using the last active mode."""

        await self.async_set_hvac_mode(self._last_on_hvac_mode)

    async def async_turn_off(self) -> None:
        """Turn the AC off."""

        await self.async_set_hvac_mode(HVACMode.OFF)

    async def _async_restore_previous_state(self) -> None:
        """Restore optimistic climate state from the recorder."""

        previous_state = await self.async_get_last_state()
        if previous_state is None:
            return

        try:
            previous_hvac_mode = HVACMode(previous_state.state)
        except ValueError:
            previous_hvac_mode = HVACMode.OFF

        if previous_hvac_mode in SUPPORTED_HVAC_MODES:
            self._attr_hvac_mode = previous_hvac_mode
            if previous_hvac_mode in ON_HVAC_MODES:
                self._last_on_hvac_mode = previous_hvac_mode

        if last_on_mode := previous_state.attributes.get(ATTR_LAST_ON_HVAC_MODE):
            try:
                last_on_hvac_mode = HVACMode(last_on_mode)
            except ValueError:
                last_on_hvac_mode = HVACMode.COOL
            if last_on_hvac_mode in ON_HVAC_MODES:
                self._last_on_hvac_mode = last_on_hvac_mode

        if (temperature := previous_state.attributes.get(ATTR_TEMPERATURE)) is not None:
            self._attr_target_temperature = _clamp_temperature(temperature)

        if (swing_mode := previous_state.attributes.get(ATTR_SWING_MODE)) in SWING_MODES:
            self._attr_swing_mode = swing_mode
            if swing_mode != SWING_3D_AUTO:
                self._last_swing_mode = swing_mode

        horizontal_restored = previous_state.attributes.get(ATTR_SWING_HORIZONTAL_MODE)
        horizontal_was_stored = horizontal_restored is not None
        if horizontal_restored in SWING_HORIZONTAL_MODES:
            self._attr_swing_horizontal_mode = horizontal_restored
            if horizontal_restored != SWING_3D_AUTO:
                self._last_swing_horizontal_mode = horizontal_restored

        if last_swing_mode := previous_state.attributes.get(ATTR_LAST_SWING_MODE):
            if last_swing_mode in SWING_MODES and last_swing_mode != SWING_3D_AUTO:
                self._last_swing_mode = last_swing_mode

        if last_swing_horizontal_mode := previous_state.attributes.get(
            ATTR_LAST_SWING_HORIZONTAL_MODE
        ):
            if (
                last_swing_horizontal_mode in SWING_HORIZONTAL_MODES
                and last_swing_horizontal_mode != SWING_3D_AUTO
            ):
                self._last_swing_horizontal_mode = last_swing_horizontal_mode

        self._reconcile_restored_swing_modes(horizontal_was_stored)

        if (
            current_temperature := previous_state.attributes.get(
                ATTR_CURRENT_TEMPERATURE
            )
        ) is not None:
            self._attr_current_temperature = _maybe_float(current_temperature)

        if (
            current_humidity := previous_state.attributes.get(ATTR_CURRENT_HUMIDITY)
        ) is not None:
            self._attr_current_humidity = _maybe_float(current_humidity)

    @callback
    def _async_tracked_state_changed(self, event: Any) -> None:
        """Update HA state when a configured source entity changes."""

        self.async_write_ha_state()

    async def _async_send_current_state(self) -> None:
        """Send an IR command representing the entity's current target state."""

        power_on = self._attr_hvac_mode != HVACMode.OFF
        mode = "heat" if self._attr_hvac_mode == HVACMode.HEAT else "cool"
        temperature = _clamp_temperature(
            self._attr_target_temperature or DEFAULT_TARGET_TEMPERATURE
        )

        try:
            command = build_mhi_ir_command(
                mode,
                temperature,
                power_on,
                base_frame_hex=self._base_frame_hex,
                swing_ud=cast(str | None, self._attr_swing_mode),
                swing_lr=cast(str | None, self._attr_swing_horizontal_mode),
            )
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err

        await infrared.async_send_command(
            self.hass,
            self._emitter_entity_id,
            command,
            context=self._context,
        )

    def _read_sensor_float(
        self,
        entity_id: str | None,
        fallback: float | None,
    ) -> float | None:
        """Read a numeric sensor state."""

        if entity_id is None:
            return fallback

        state = self.hass.states.get(entity_id)
        if state is None:
            return fallback

        return _state_float(state, fallback)

    def _set_vertical_swing_mode(self, swing_mode: str) -> None:
        """Update vertical swing and keep 3D Auto axes coupled."""

        if swing_mode == SWING_3D_AUTO:
            self._attr_swing_mode = SWING_3D_AUTO
            self._attr_swing_horizontal_mode = SWING_3D_AUTO
            return

        self._attr_swing_mode = swing_mode
        self._last_swing_mode = swing_mode

        if self._attr_swing_horizontal_mode == SWING_3D_AUTO:
            self._attr_swing_horizontal_mode = (
                self._last_swing_horizontal_mode or SWING_STOP
            )

        if self._attr_swing_horizontal_mode != SWING_3D_AUTO:
            self._last_swing_horizontal_mode = self._attr_swing_horizontal_mode

    def _set_horizontal_swing_mode(self, swing_horizontal_mode: str) -> None:
        """Update horizontal swing and keep 3D Auto axes coupled."""

        if swing_horizontal_mode == SWING_3D_AUTO:
            self._attr_swing_mode = SWING_3D_AUTO
            self._attr_swing_horizontal_mode = SWING_3D_AUTO
            return

        self._attr_swing_horizontal_mode = swing_horizontal_mode
        self._last_swing_horizontal_mode = swing_horizontal_mode

        if self._attr_swing_mode == SWING_3D_AUTO:
            self._attr_swing_mode = self._last_swing_mode or SWING_STOP

        if self._attr_swing_mode != SWING_3D_AUTO:
            self._last_swing_mode = self._attr_swing_mode

    def _reconcile_restored_swing_modes(self, horizontal_was_stored: bool) -> None:
        """Normalize restored swing state after upgrades or partial attributes."""

        if not horizontal_was_stored and self._attr_swing_mode != SWING_3D_AUTO:
            self._attr_swing_horizontal_mode = (
                self._last_swing_horizontal_mode or SWING_STOP
            )

        if (
            self._attr_swing_mode == SWING_3D_AUTO
            or self._attr_swing_horizontal_mode == SWING_3D_AUTO
        ):
            self._attr_swing_mode = SWING_3D_AUTO
            self._attr_swing_horizontal_mode = SWING_3D_AUTO
            return

        self._last_swing_mode = self._attr_swing_mode
        self._last_swing_horizontal_mode = self._attr_swing_horizontal_mode


def _optional_entity_id(value: Any) -> str | None:
    """Normalize optional entity IDs from config data."""

    if value in (None, ""):
        return None
    return str(value)


def _coerce_hvac_mode(value: HVACMode | str) -> HVACMode:
    """Coerce a service value to HVACMode."""

    try:
        return HVACMode(value)
    except ValueError as err:
        raise HomeAssistantError(f"Unsupported HVAC mode: {value}") from err


def _clamp_temperature(value: Any) -> int:
    """Clamp and round a target temperature to the supported MHI range."""

    temperature = round(float(value))
    return min(MAX_TARGET_TEMPERATURE, max(MIN_TARGET_TEMPERATURE, temperature))


def _state_float(state: State, fallback: float | None) -> float | None:
    """Convert a state object to float when available."""

    if state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
        return fallback

    return _maybe_float(state.state, fallback)


def _maybe_float(value: Any, fallback: float | None = None) -> float | None:
    """Convert a value to float or return a fallback."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback
