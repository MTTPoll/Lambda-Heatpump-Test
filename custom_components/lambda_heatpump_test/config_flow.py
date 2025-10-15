
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS
import homeassistant.helpers.config_validation as cv

from . import DOMAIN

class LambdaHeatpumpTestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        SCHEMA = vol.Schema({
            vol.Required(CONF_IP_ADDRESS): cv.string,
            vol.Optional("update_interval", default=30): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600)),
            vol.Required("installed_before_2025", default=False): cv.boolean,
            vol.Optional("has_heat_circuit_2", default=True): cv.boolean,
            vol.Optional("has_heat_circuit_3", default=True): cv.boolean,
                vol.Optional("unit_id", default=1): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
        })

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)

        word_order = "big" if user_input.get("installed_before_2025") else "little"

        data = {
            "ip_address": user_input["ip_address"],
            "update_interval": user_input.get("update_interval", 30),
            "has_heat_circuit_2": user_input.get("has_heat_circuit_2", True),
            "has_heat_circuit_3": user_input.get("has_heat_circuit_3", True),
            "word_order": word_order,
                "unit_id": user_input.get("unit_id", 1),
        }
        title = f"Lambda Heatpump Test ({user_input['ip_address']})"
        return self.async_create_entry(title=title, data=data)
