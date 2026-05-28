"""Config flow para la integración EMASESA."""
from __future__ import annotations
import logging
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from .api import EmasesaApiClient, EmasesaApiError, EmasesaAuthError
from .const import CONF_CONTRATO, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Required(CONF_CONTRATO): str,
    vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): vol.All(int, vol.Range(min=300)),
})


class EmasesaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flujo de configuración para EMASESA."""
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_CONTRATO])
            self._abort_if_unique_id_configured()
            client = EmasesaApiClient(
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                contrato=user_input[CONF_CONTRATO],
            )
            try:
                await self.hass.async_add_executor_job(client.authenticate)
            except EmasesaAuthError:
                errors["base"] = "invalid_auth"
            except EmasesaApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Error inesperado")
                errors["base"] = "unknown"
            if not errors:
                return self.async_create_entry(
                    title=f"EMASESA - Contrato {user_input[CONF_CONTRATO]}",
                    data=user_input,
                )
        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)
