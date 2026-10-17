"""Entity-state tests for the Eco and Boost 3D Auto rules."""

from __future__ import annotations

from enum import Enum, IntFlag
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock


def _module(name: str, *, package: bool = False, **attributes: object) -> ModuleType:
    module = ModuleType(name)
    if package:
        module.__path__ = []
    for attribute, value in attributes.items():
        setattr(module, attribute, value)
    sys.modules[name] = module
    return module


class HVACMode(str, Enum):
    OFF = "off"
    COOL = "cool"
    HEAT = "heat"
    DRY = "dry"
    FAN_ONLY = "fan_only"
    HEAT_COOL = "heat_cool"


class ClimateEntityFeature(IntFlag):
    TARGET_TEMPERATURE = 1
    FAN_MODE = 2
    PRESET_MODE = 4
    SWING_MODE = 8
    SWING_HORIZONTAL_MODE = 16
    TURN_ON = 32
    TURN_OFF = 64


class ClimateEntity:
    _context = None

    async def async_added_to_hass(self) -> None:
        return None

    def async_on_remove(self, callback: object) -> object:
        return callback

    def async_write_ha_state(self) -> None:
        return None


class RestoreEntity:
    async def async_get_last_state(self) -> object | None:
        return None

    async def async_get_last_extra_data(self) -> object | None:
        return None


class HomeAssistantError(Exception):
    """Minimal Home Assistant service error."""


class Platform(str, Enum):
    CLIMATE = "climate"
    SELECT = "select"
    BUTTON = "button"
    SWITCH = "switch"


class UnitOfTemperature(str, Enum):
    CELSIUS = "°C"


class _Command:
    def __init__(self, **kwargs: int) -> None:
        self.modulation = kwargs.get("modulation")
        self.repeat_count = kwargs.get("repeat_count")


def _cancel_callback() -> None:
    return None


def _async_call_later(*_args: object, **_kwargs: object):
    return _cancel_callback


def _install_home_assistant_stubs() -> None:
    _module("homeassistant", package=True)
    _module("homeassistant.components", package=True)
    _module(
        "homeassistant.components.infrared",
        async_send_command=AsyncMock(),
    )
    _module(
        "homeassistant.components.climate",
        ClimateEntity=ClimateEntity,
        ClimateEntityFeature=ClimateEntityFeature,
    )
    _module(
        "homeassistant.components.climate.const",
        ATTR_CURRENT_HUMIDITY="current_humidity",
        ATTR_CURRENT_TEMPERATURE="current_temperature",
        ATTR_FAN_MODE="fan_mode",
        ATTR_HVAC_MODE="hvac_mode",
        ATTR_PRESET_MODE="preset_mode",
        ATTR_SWING_HORIZONTAL_MODE="swing_horizontal_mode",
        ATTR_SWING_MODE="swing_mode",
        HVACMode=HVACMode,
        PRESET_BOOST="boost",
        PRESET_NONE="none",
    )
    _module("homeassistant.config_entries", ConfigEntry=object)
    _module(
        "homeassistant.const",
        ATTR_TEMPERATURE="temperature",
        CONF_NAME="name",
        PRECISION_TENTHS=0.1,
        STATE_UNAVAILABLE="unavailable",
        STATE_UNKNOWN="unknown",
        UnitOfTemperature=UnitOfTemperature,
        Platform=Platform,
    )
    _module(
        "homeassistant.core",
        HomeAssistant=object,
        State=object,
        callback=lambda function: function,
    )
    _module("homeassistant.exceptions", HomeAssistantError=HomeAssistantError)
    _module("homeassistant.helpers", package=True)
    _module(
        "homeassistant.helpers.entity_platform",
        AddEntitiesCallback=object,
    )
    _module(
        "homeassistant.helpers.event",
        async_call_later=_async_call_later,
        async_track_state_change_event=lambda *_args, **_kwargs: _cancel_callback,
    )
    _module(
        "homeassistant.helpers.restore_state",
        RestoreEntity=RestoreEntity,
        ExtraStoredData=object,
    )

    infrared_protocols = _module("infrared_protocols", package=True)
    commands = _module("infrared_protocols.commands", Command=_Command)
    infrared_protocols.commands = commands


REPOSITORY_ROOT = Path(__file__).parents[1]
_install_home_assistant_stubs()
custom_components = _module("custom_components", package=True)
custom_components.__path__ = [str(REPOSITORY_ROOT / "custom_components")]
mhi_package = _module("custom_components.mhi_ir_climate", package=True)
mhi_package.__path__ = [
    str(REPOSITORY_ROOT / "custom_components" / "mhi_ir_climate")
]
climate = importlib.import_module("custom_components.mhi_ir_climate.climate")


class EcoClimateEntityTest(unittest.IsolatedAsyncioTestCase):
    """Verify Eco availability, persistence, and swing conflicts."""

    def _entity(self):
        entry = SimpleNamespace(unique_id="test", entry_id="test")
        data = {
            "config": {
                climate.CONF_EMITTER_ENTITY_ID: "infrared.test",
                climate.CONF_BASE_FRAME_HEX: (
                    "52aec31ae5f609f807ff004db25aa5ff007f80"
                ),
                "name": "Test AC",
            }
        }
        entity = climate.MHIIRClimateEntity(object(), entry, data)
        entity._async_send_current_state = AsyncMock()
        return entity

    async def test_eco_availability_and_no_timeout(self) -> None:
        for hvac_mode in (
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.DRY,
            HVACMode.HEAT_COOL,
        ):
            with self.subTest(hvac_mode=hvac_mode):
                entity = self._entity()
                entity._attr_hvac_mode = hvac_mode
                await entity.async_set_preset_mode("Eco")
                self.assertEqual(entity._attr_preset_mode, "eco")
                self.assertIsNone(entity._cancel_boost_reset)

        for hvac_mode in (HVACMode.OFF, HVACMode.FAN_ONLY):
            with self.subTest(hvac_mode=hvac_mode):
                entity = self._entity()
                entity._attr_hvac_mode = hvac_mode
                with self.assertRaises(HomeAssistantError):
                    await entity.async_set_preset_mode("Eco")
                self.assertEqual(entity._attr_preset_mode, "none")
                entity._async_send_current_state.assert_not_awaited()

    async def test_eco_survives_supported_mode_and_clears_in_fan_only(self) -> None:
        entity = self._entity()
        entity._attr_hvac_mode = HVACMode.COOL
        entity._attr_swing_mode = "Stop"
        entity._attr_swing_horizontal_mode = "Stop"
        await entity.async_set_preset_mode("Eco")

        await entity.async_set_hvac_mode(HVACMode.DRY)
        self.assertEqual(entity._attr_preset_mode, "eco")
        await entity.async_set_hvac_mode(HVACMode.HEAT)
        self.assertEqual(entity._attr_preset_mode, "eco")
        await entity.async_set_hvac_mode(HVACMode.FAN_ONLY)
        self.assertEqual(entity._attr_preset_mode, "none")

        entity._attr_hvac_mode = HVACMode.COOL
        await entity.async_set_preset_mode("eco")
        await entity.async_set_hvac_mode(HVACMode.OFF)
        self.assertEqual(entity._attr_preset_mode, "none")

    async def test_eco_preserves_selected_fan_mode_in_entity_state(self) -> None:
        entity = self._entity()
        entity._attr_hvac_mode = HVACMode.COOL
        entity._attr_fan_mode = "High"

        await entity.async_set_preset_mode("eco")
        self.assertEqual(entity._attr_fan_mode, "High")

        await entity.async_set_fan_mode("Low")
        self.assertEqual(entity._attr_fan_mode, "Low")
        self.assertEqual(entity._attr_preset_mode, "eco")

    async def test_enabling_eco_or_boost_exits_3d_auto(self) -> None:
        for preset_mode in ("eco", "boost"):
            with self.subTest(preset_mode=preset_mode):
                entity = self._entity()
                entity._attr_hvac_mode = HVACMode.COOL
                entity._last_swing_mode = "30 Deg"
                entity._last_swing_horizontal_mode = "Left"

                await entity.async_set_preset_mode(preset_mode)

                self.assertEqual(entity._attr_swing_mode, "30 Deg")
                self.assertEqual(entity._attr_swing_horizontal_mode, "Left")
                if preset_mode == "boost":
                    self.assertIsNotNone(entity._cancel_boost_reset)
                else:
                    self.assertIsNone(entity._cancel_boost_reset)

    async def test_enabling_conflicting_preset_falls_back_to_stop(self) -> None:
        entity = self._entity()
        entity._attr_hvac_mode = HVACMode.COOL

        await entity.async_set_preset_mode("eco")

        self.assertEqual(entity._attr_swing_mode, "Stop")
        self.assertEqual(entity._attr_swing_horizontal_mode, "Stop")

    async def test_3d_auto_requests_are_rejected_without_sending(self) -> None:
        for preset_mode in ("eco", "boost"):
            with self.subTest(preset_mode=preset_mode):
                entity = self._entity()
                entity._attr_hvac_mode = HVACMode.COOL
                entity._attr_preset_mode = preset_mode
                entity._attr_swing_mode = "30 Deg"
                entity._attr_swing_horizontal_mode = "Left"

                with self.assertRaises(HomeAssistantError):
                    await entity.async_set_swing_mode("3D Auto")
                with self.assertRaises(HomeAssistantError):
                    await entity.async_set_swing_horizontal_mode("3D Auto")

                self.assertEqual(entity._attr_swing_mode, "30 Deg")
                self.assertEqual(entity._attr_swing_horizontal_mode, "Left")
                entity._async_send_current_state.assert_not_awaited()

    async def test_restored_eco_in_dry_mode_is_retained_and_reconciled(self) -> None:
        entity = self._entity()
        previous_state = SimpleNamespace(
            state="dry",
            attributes={
                "temperature": 24,
                "fan_mode": "Low",
                "preset_mode": "Eco",
                "swing_mode": "3D Auto",
                "swing_horizontal_mode": "3D Auto",
            },
        )
        entity.async_get_last_state = AsyncMock(return_value=previous_state)

        await entity._async_restore_previous_state()

        self.assertEqual(entity._attr_hvac_mode, HVACMode.DRY)
        self.assertEqual(entity._attr_preset_mode, "eco")
        self.assertEqual(entity._attr_swing_mode, "Stop")
        self.assertEqual(entity._attr_swing_horizontal_mode, "Stop")
        self.assertIsNone(entity._cancel_boost_reset)


if __name__ == "__main__":
    unittest.main()
