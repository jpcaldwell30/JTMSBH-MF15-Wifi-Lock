"""Config flow for JTMSBH MF15 Wifi Lock."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant

from .const import DOMAIN, TUYA_DOMAIN, CONF_ACCESS_ID, CONF_ACCESS_SECRET
from .tuya_helper import is_tuya_integration_available

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_ACCESS_ID): str,
    vol.Required(CONF_ACCESS_SECRET): str,
})


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    # Check if Tuya integration is available
    if not is_tuya_integration_available(hass):
        raise ValueError("tuya_not_found")
    
    # Validate that required fields are provided
    access_id = data.get(CONF_ACCESS_ID, "").strip()
    access_secret = data.get(CONF_ACCESS_SECRET, "").strip()
    
    if not access_id:
        raise ValueError("missing_access_id")
    if not access_secret:
        raise ValueError("missing_access_secret")
    
    # Basic validation of credential format
    if len(access_id) < 10:
        raise ValueError("invalid_access_id")
    if len(access_secret) < 20:
        raise ValueError("invalid_access_secret")

    return {"title": "JTMSBH MF15 Wifi Lock"}


class JTMSBHConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for JTMSBH MF15 Wifi Lock."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except ValueError as error:
                error_str = str(error)
                if error_str == "tuya_not_found":
                    errors["base"] = "tuya_not_found"
                elif error_str in ["missing_access_id", "invalid_access_id"]:
                    errors["access_id"] = error_str
                elif error_str in ["missing_access_secret", "invalid_access_secret"]:
                    errors["access_secret"] = error_str
                else:
                    errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"], 
                    data={
                        CONF_ACCESS_ID: user_input[CONF_ACCESS_ID].strip(),
                        CONF_ACCESS_SECRET: user_input[CONF_ACCESS_SECRET].strip(),
                    }
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle reauth flow to add missing API credentials."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth confirmation to add API credentials."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except ValueError as error:
                error_str = str(error)
                if error_str in ["missing_access_id", "invalid_access_id"]:
                    errors["access_id"] = error_str
                elif error_str in ["missing_access_secret", "invalid_access_secret"]:
                    errors["access_secret"] = error_str
                else:
                    errors["base"] = "unknown"
            else:
                # Update the existing config entry with new credentials
                existing_entry = await self.async_set_unique_id(DOMAIN)
                if existing_entry:
                    self.hass.config_entries.async_update_entry(
                        existing_entry,
                        data={
                            **existing_entry.data,
                            CONF_ACCESS_ID: user_input[CONF_ACCESS_ID].strip(),
                            CONF_ACCESS_SECRET: user_input[CONF_ACCESS_SECRET].strip(),
                        },
                    )
                    await self.hass.config_entries.async_reload(existing_entry.entry_id)
                    return self.async_abort(reason="reauth_successful")
                
                return self.async_abort(reason="reauth_failed")
        
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "reason": "Missing API credentials from previous setup"
            },
        )