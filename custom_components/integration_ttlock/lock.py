"""Binary sensor platform for integration_blueprint."""
from homeassistant.components.lock import LockEntity
from homeassistant.core import Context


from custom_components.integration_ttlock.ttlock import (
    extract_lock_status_from_records_with_lock_id,
)

from .const import (
    DOMAIN,
    LOCK,
)
from .entity import TTLockEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup lock platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    for lock_data in coordinator.data["locks"].values():
        async_add_devices([TTLockLock(coordinator, entry, lock_data)])


class TTLockLock(TTLockEntity, LockEntity):
    """integration_blueprint binary_sensor class."""

    def __init__(self, coordinator, config_entry, lock_data):
        super().__init__(coordinator, config_entry, lock_data)

        self.lock_state = 2
        self.refresh_type = self.config_entry.options.get("refresh_type", "Polling")
        self.lock_state_changed_by = None

    async def async_update(self):
        if self.refresh_type == "Polling":
            response = await self.coordinator.api.query_open_state(self.lock_id)

            if "state" in response:
                self.lock_state = int(response["state"])
                self.lock_state_changed_by = None
        elif self.refresh_type == "Polling Logs":
            records = await self.coordinator.api.list_lock_record(self.lock_id)
            (
                self.lock_state,
                self.lock_state_changed_by,
            ) = extract_lock_status_from_records_with_lock_id(self.lock_id, records)

    @property
    def changed_by(self):
        return self.lock_state_changed_by

    @property
    def should_poll(self):
        """Should home assistant poll the data"""
        return self.refresh_type in ["Polling", "Polling Logs"]

    @property
    def is_locked(self):
        """Return lock state"""
        if self.lock_state >= 2:
            return None
        return self.lock_state == 0

    @property
    def name(self):
        """Return the name of the lock."""
        return self.lock_data["lockAlias"]

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return str(self.lock_id) + "_" + LOCK

    async def async_lock(self, **kwargs):
        """Lock all or specified locks"""
        await self.coordinator.api.lock_lock(self.lock_id)

    async def async_unlock(self, **kwargs):
        """Lock all or specified locks"""
        await self.coordinator.api.lock_unlock(self.lock_id)
