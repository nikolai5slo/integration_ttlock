"""Adds config flow for Blueprint."""
import logging
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
import voluptuous as vol

from .ttlock_api import TTLockApiClient

from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_REFRESH_TOKEN,
    INPUT_PASSWORD,
    CONF_SERVER,
    CONF_USERNAME,
    DOMAIN,
)


_LOGGER: logging.Logger = logging.getLogger(__package__)


class TTLockFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for TTLock."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            token = await self._get_refresh_token(
                user_input[CONF_SERVER],
                user_input[CONF_CLIENT_ID],
                user_input[CONF_CLIENT_SECRET],
                user_input[CONF_USERNAME],
                user_input[INPUT_PASSWORD],
            )
            if token is not None:
                d = {
                    CONF_SERVER: user_input[CONF_SERVER],
                    CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
                    CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET],
                    CONF_USERNAME: user_input[CONF_USERNAME],
                    CONF_REFRESH_TOKEN: token,
                }
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data=d,
                )

            self._errors["base"] = "auth"

            return await self._show_config_form(user_input)

        user_input = {}
        # Provide defaults for form
        user_input[CONF_SERVER] = "https://euapi.ttlock.com"

        user_input[CONF_CLIENT_ID] = ""
        user_input[CONF_CLIENT_SECRET] = ""

        user_input[CONF_USERNAME] = ""
        user_input[INPUT_PASSWORD] = ""

        return await self._show_config_form(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TTLockOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SERVER, default=user_input[CONF_SERVER]): str,
                    vol.Required(
                        CONF_CLIENT_ID, default=user_input[CONF_CLIENT_ID]
                    ): str,
                    vol.Required(
                        CONF_CLIENT_SECRET, default=user_input[CONF_CLIENT_SECRET]
                    ): str,
                    vol.Required(CONF_USERNAME, default=user_input[CONF_USERNAME]): str,
                    vol.Required(
                        INPUT_PASSWORD, default=user_input[INPUT_PASSWORD]
                    ): str,
                }
            ),
            errors=self._errors,
        )

    async def _get_refresh_token(
        self, url: str, client_id: str, client_secret: str, username: str, password: str
    ):
        """Return refresh token if credentials is valid or None if invalid."""
        try:
            session = async_create_clientsession(self.hass)
            client = TTLockApiClient(url, client_id, client_secret, username, session)
            data = await client.async_authenticate(password, "password")
            if "refresh_token" in data:
                return data["refresh_token"]
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Exception %s", exception)
        return None


class TTLockOptionsFlowHandler(config_entries.OptionsFlow):
    """TTLock config flow options handler."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "refresh_type",
                        default=self.options.get("refresh_type", "Polling"),
                    ): selector(
                        {
                            "select": {
                                "options": ["Polling", "Polling Logs", "Webhook Logs"],
                            }
                        }
                    )
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_USERNAME), data=self.options
        )
