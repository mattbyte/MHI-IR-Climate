"""Constants for the MHI IR Climate integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "mhi_ir_climate"
PLATFORMS = [Platform.CLIMATE, Platform.SELECT, Platform.BUTTON, Platform.SWITCH]

CONF_BASE_FRAME_HEX = "base_frame_hex"
CONF_EMITTER_ENTITY_ID = "emitter_entity_id"
CONF_HUMIDITY_SENSOR = "humidity_sensor"
CONF_TEMPERATURE_SENSOR = "temperature_sensor"

DEFAULT_NAME = "MHI Air Conditioner"

DEVICE_MODEL = "MHI ZSA Series (Avanti)"

ATTR_INFRARED_EMITTER_ENTITY_ID = "infrared_emitter_entity_id"
ATTR_LAST_ON_HVAC_MODE = "last_on_hvac_mode"
ATTR_LAST_SWING_HORIZONTAL_MODE = "last_swing_horizontal_mode"
ATTR_LAST_SWING_MODE = "last_swing_mode"
ATTR_MODEL = "model"
