"""Constants for the MHI IR Climate integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "mhi_ir_climate"
PLATFORMS = [Platform.CLIMATE]

CONF_BASE_FRAME_HEX = "base_frame_hex"
CONF_EMITTER_ENTITY_ID = "emitter_entity_id"
CONF_HUMIDITY_SENSOR = "humidity_sensor"
CONF_MODEL = "model"
CONF_TEMPERATURE_SENSOR = "temperature_sensor"

DEFAULT_NAME = "MHI Air Conditioner"

MODEL_DXK09ZSA_W = "dxk09zsa_w"
MODEL_SRK35ZSA_W = "srk35zsa_w"
MODEL_ZSA_SERIES = "zsa_series"

MODEL_LABELS = {
    MODEL_ZSA_SERIES: "MHI ZSA series (RLA502A700L/RLA502A720)",
    MODEL_DXK09ZSA_W: "DXK09ZSA-W (remote RLA502A720)",
    MODEL_SRK35ZSA_W: "SRK35ZSA-W (remote RLA502A700L)",
}

DEFAULT_MODEL = MODEL_ZSA_SERIES

ATTR_INFRARED_EMITTER_ENTITY_ID = "infrared_emitter_entity_id"
ATTR_LAST_ON_HVAC_MODE = "last_on_hvac_mode"
ATTR_MODEL = "model"
