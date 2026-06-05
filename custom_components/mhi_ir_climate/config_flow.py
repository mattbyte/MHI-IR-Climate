"""Config flow for MHI IR Climate."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import infrared
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.util import slugify

from .const import (
    CONF_BASE_FRAME_HEX,
    CONF_EMITTER_ENTITY_ID,
    CONF_HUMIDITY_SENSOR,
    CONF_MODEL,
    CONF_TEMPERATURE_SENSOR,
    DEFAULT_MODEL,
    DEFAULT_NAME,
    DOMAIN,
    MODEL_LABELS,
)
from .ir_protocol import DEFAULT_BASE_FRAME_HEX, validate_base_frame_hex


class MHIIRClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MHI IR Climate."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""

        return MHIIRClimateOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Create an MHI IR climate entity."""

        emitters = set(infrared.async_get_emitters(self.hass))
        if not emitters:
            return self.async_abort(reason="no_emitters")

        errors: dict[str, str] = {}

        if user_input is not None:
            errors = _validate_input(user_input, emitters)
            if not errors:
                name = user_input[CONF_NAME]
                unique_id = f"{slugify(name)}_{user_input[CONF_EMITTER_ENTITY_ID]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=name, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(),
            errors=errors,
        )


class MHIIRClimateOptionsFlow(config_entries.OptionsFlow):
    """Handle options for MHI IR Climate."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Update options."""

        data = {**self.config_entry.data, **self.config_entry.options}
        emitters = set(infrared.async_get_emitters(self.hass))
        current_emitter = data.get(CONF_EMITTER_ENTITY_ID)
        if current_emitter:
            emitters.add(current_emitter)

        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate_input(user_input, emitters)
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(data),
            errors=errors,
        )


def _validate_input(user_input: dict[str, Any], emitters: set[str]) -> dict[str, str]:
    """Validate config flow input."""

    errors: dict[str, str] = {}

    if user_input[CONF_EMITTER_ENTITY_ID] not in emitters:
        errors[CONF_EMITTER_ENTITY_ID] = "invalid_emitter"

    try:
        validate_base_frame_hex(user_input[CONF_BASE_FRAME_HEX])
    except ValueError:
        errors[CONF_BASE_FRAME_HEX] = "invalid_base_frame"

    return errors


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the flow schema."""

    defaults = defaults or {}
    emitter_default = defaults.get(CONF_EMITTER_ENTITY_ID)
    emitter_marker = (
        vol.Required(CONF_EMITTER_ENTITY_ID, default=emitter_default)
        if emitter_default
        else vol.Required(CONF_EMITTER_ENTITY_ID)
    )
    schema: dict[vol.Marker, Any] = {
        vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
        emitter_marker: selector.EntitySelector(
            selector.EntitySelectorConfig(domain="infrared"),
        ),
        vol.Required(
            CONF_MODEL,
            default=defaults.get(CONF_MODEL, DEFAULT_MODEL),
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    {"value": value, "label": label}
                    for value, label in MODEL_LABELS.items()
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(
            CONF_BASE_FRAME_HEX,
            default=defaults.get(CONF_BASE_FRAME_HEX, DEFAULT_BASE_FRAME_HEX),
        ): str,
    }

    _add_optional_entity_selector(schema, CONF_TEMPERATURE_SENSOR, defaults)
    _add_optional_entity_selector(schema, CONF_HUMIDITY_SENSOR, defaults)

    return vol.Schema(schema)


def _add_optional_entity_selector(
    schema: dict[vol.Marker, Any],
    key: str,
    defaults: dict[str, Any],
) -> None:
    """Add an optional sensor entity selector to a schema."""

    default = defaults.get(key)
    marker = vol.Optional(key, default=default) if default else vol.Optional(key)
    schema[marker] = selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor"),
    )
