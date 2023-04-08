"""
Custom integration to integrate integration_blueprint with Home Assistant.

For more details about this integration, please refer to
https://github.com/custom-components/integration_blueprint
"""
import asyncio
from datetime import timedelta
import hashlib
import json
import logging
from urllib.parse import parse_qs

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import traceback
from custom_components.integration_ttlock.ttlock import extract_lock_status_from_records


from .ttlock_api import TTLockApiClient
from .validators import validate_lock_data

from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_REFRESH_TOKEN,
    CONF_SERVER,
    CONF_USERNAME,
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
)

SCAN_INTERVAL = timedelta(seconds=30)
DEPENDENCIES = ["webhook"]

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using YAML is not supported."""
    del hass, entry
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    url = entry.data.get(CONF_SERVER)
    client_id = entry.data.get(CONF_CLIENT_ID)
    client_secret = entry.data.get(CONF_CLIENT_SECRET)
    username = entry.data.get(CONF_USERNAME)
    refresh_token = entry.data.get(CONF_REFRESH_TOKEN)

    session = async_get_clientsession(hass)
    client = TTLockApiClient(url, client_id, client_secret, username, session)

    def on_token_refresh(new_token: str):
        entry_data = entry.data.copy()
        entry_data[CONF_REFRESH_TOKEN] = new_token
        hass.config_entries.async_update_entry(entry, data=entry_data)

    client.on_new_refresh_token(on_token_refresh)
    data = await client.async_authenticate(refresh_token, "refresh_token")
    if "access_token" not in data:
        raise ConfigEntryNotReady("Invalid credentials")

    coordinator = TTLockDataUpdateCoordinator(hass, client=client)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    if entry.options.get("refresh_type") == "Webhook Logs":
        webhook_id = entry.options.get(
            "webhook_id", hashlib.md5((client_id + client_secret).encode()).hexdigest()
        )

        hass.components.webhook.async_register(
            DOMAIN,
            "TTLock",
            webhook_id,
            lambda hass, webhook_id, request: handle_webhook(
                entry, hass, webhook_id, request
            ),
        )

        url = hass.components.webhook.async_generate_url(webhook_id)
        _LOGGER.debug("webhook data: %s", url)
        print("Webhook data %s" % url)

    for platform in PLATFORMS:
        coordinator.platforms.append(platform)
        hass.async_add_job(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


class TTLockDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, client: TTLockApiClient) -> None:
        """Initialize."""
        self.api = client
        self.platforms = []

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self):
        """Update data via library."""
        try:
            locks = await self.api.list_lock()

            locks = filter(validate_lock_data, locks)

            return {
                "locks": {data["lockId"]: data for data in locks},
                "states": {},
            }
        except Exception as exception:
            traceback.print_exc()
            raise UpdateFailed() from exception


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def handle_webhook(entry, hass, webhook_id, request):
    """Handle webhook callback."""
    _LOGGER.info("webhook called")

    body = await request.text()
    data = parse_qs(body)
    lockId = int(data["lockId"])

    records_str = data["records"][0]
    records = json.loads(records_str)

    (
        lock_state,
        lock_state_changed_by,
    ) = extract_lock_status_from_records(records)

    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.data[lockId]["state"] = lock_state
    coordinator.data[lockId]["state_changed_by"] = lock_state_changed_by

    return "success"
