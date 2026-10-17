"""Regression coverage for settings lost while the IR emitter is unavailable."""

import json
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock

from test_climate_eco import climate, HVACMode


class ClimateRestoreTest(unittest.IsolatedAsyncioTestCase):
    def entity(self, emitter=None):
        hass = SimpleNamespace(states=SimpleNamespace(get=lambda _: emitter))
        entity = climate.MHIIRClimateEntity(
            hass,
            SimpleNamespace(unique_id="restore", entry_id="restore"),
            {"config": {
                climate.CONF_EMITTER_ENTITY_ID: "infrared.test",
                climate.CONF_BASE_FRAME_HEX: "52aec31ae5f609f807ff004db25aa5ff007f80",
                "name": "Restore AC",
            }},
        )
        entity._async_send_current_state = AsyncMock()
        return entity

    async def restore(self, entity, extra=None, state=None):
        entity.async_get_last_state = AsyncMock(return_value=state)
        entity.async_get_last_extra_data = AsyncMock(
            return_value=SimpleNamespace(as_dict=lambda: extra) if extra is not None else None
        )
        await entity._async_restore_previous_state()

    async def test_repeated_unavailable_restarts_preserve_complete_snapshot(self):
        entity = self.entity()
        entity._attr_hvac_mode = HVACMode.HEAT
        entity._last_on_hvac_mode = HVACMode.HEAT
        entity._attr_target_temperature = 21
        entity._attr_fan_mode = "High"
        entity._attr_preset_mode = "eco"
        entity._attr_swing_mode = "30 Deg"
        entity._attr_swing_horizontal_mode = "Left"
        entity._last_swing_mode = "30 Deg"
        entity._last_swing_horizontal_mode = "Left"
        entity._attr_current_temperature = 19.5
        entity._attr_current_humidity = 65
        expected = json.loads(json.dumps(entity.extra_restore_state_data.as_dict()))
        for emitter in (None, SimpleNamespace(state="unavailable"), None):
            snapshot = json.loads(json.dumps(entity.extra_restore_state_data.as_dict()))
            entity = self.entity(emitter)
            await self.restore(entity, snapshot, SimpleNamespace(state="unavailable", attributes={}))
            self.assertFalse(entity.available)
            self.assertEqual(entity.extra_restore_state_data.as_dict(), expected)
            entity._async_send_current_state.assert_not_awaited()
        entity.hass.states.get = lambda _: SimpleNamespace(state="ready")
        entity._async_tracked_state_changed(None)
        self.assertTrue(entity.available)
        self.assertEqual(entity.extra_restore_state_data.as_dict(), expected)
        entity._async_send_current_state.assert_not_awaited()

    async def test_off_restores_last_mode_for_explicit_turn_on(self):
        entity = self.entity()
        await self.restore(entity, {
            "version": 1, "hvac_mode": "off", "last_on_hvac_mode": "heat",
            "temperature": 21,
        }, SimpleNamespace(state="unavailable", attributes={}))
        self.assertEqual(entity._attr_hvac_mode, HVACMode.OFF)
        entity._async_send_current_state.assert_not_awaited()
        await entity.async_turn_on()
        self.assertEqual(entity._attr_hvac_mode, HVACMode.HEAT)
        self.assertEqual(entity._attr_target_temperature, 21)
        entity._async_send_current_state.assert_awaited_once()

    async def test_extra_wins_and_invalid_fields_use_legacy(self):
        entity = self.entity()
        await self.restore(entity, {
            "version": 1, "hvac_mode": "heat", "last_on_hvac_mode": [],
            "temperature": "bad", "fan_mode": {}, "preset_mode": [],
        }, SimpleNamespace(state="cool", attributes={"temperature": 22, "fan_mode": "High"}))
        self.assertEqual(entity._attr_hvac_mode, HVACMode.HEAT)
        self.assertEqual(entity._last_on_hvac_mode, HVACMode.HEAT)
        self.assertEqual(entity._attr_target_temperature, 22)
        self.assertEqual(entity._attr_fan_mode, "High")

    async def test_nonfinite_and_invalid_temperatures_fall_back(self):
        for value in (float("nan"), float("inf"), float("-inf"), "bad", {}, True):
            with self.subTest(value=value):
                entity = self.entity()
                await self.restore(entity, {"version": 1, "temperature": value},
                                   SimpleNamespace(state="heat", attributes={"temperature": 21}))
                self.assertEqual(entity._attr_target_temperature, 21)

    async def test_legacy_and_unknown_versions_restore_without_extra(self):
        for extra in (None, {"version": 99, "temperature": 24}, []):
            entity = self.entity()
            await self.restore(entity, extra, SimpleNamespace(state="heat", attributes={"temperature": 21}))
            self.assertEqual(entity._attr_target_temperature, 21)
            self.assertEqual(entity._last_on_hvac_mode, HVACMode.HEAT)

    async def test_extra_without_legacy_and_temperature_clamping(self):
        for temperature, expected in ((10, 18), (40, 30)):
            entity = self.entity()
            await self.restore(entity, {"version": 1, "hvac_mode": "heat", "temperature": temperature})
            self.assertEqual(entity._attr_target_temperature, expected)

    async def test_first_setup_quiet_but_unrecoverable_saved_state_warns(self):
        entity = self.entity()
        with self.assertNoLogs(climate._LOGGER, level="WARNING"):
            await self.restore(entity)
        with self.assertLogs(climate._LOGGER, level="WARNING"):
            await self.restore(entity, state=SimpleNamespace(state="unknown", attributes={}))
        self.assertEqual(entity._attr_hvac_mode, HVACMode.OFF)
        self.assertEqual(entity._attr_target_temperature, 24)
        entity._async_send_current_state.assert_not_awaited()

    async def test_restored_boost_and_dry_rules_still_apply(self):
        entity = self.entity()
        await self.restore(entity, {"version": 1, "hvac_mode": "heat", "temperature": 21, "preset_mode": "boost"})
        self.assertIsNotNone(entity._cancel_boost_reset)
        self.assertEqual(entity._attr_swing_mode, "Stop")
        entity._async_send_current_state.assert_not_awaited()
        entity = self.entity()
        await self.restore(entity, {"version": 1, "hvac_mode": "dry", "temperature": 21, "fan_mode": "High"})
        self.assertEqual(entity._attr_fan_mode, "Auto")
        self.assertEqual(entity._attr_swing_mode, "Stop")
