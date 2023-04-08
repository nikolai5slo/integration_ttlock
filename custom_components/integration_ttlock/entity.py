"""BlueprintEntity class"""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import callback

from .const import DOMAIN


class TTLockEntity(CoordinatorEntity):
    """TTLock Base entity"""

    def __init__(self, coordinator, config_entry, lock_data):
        super().__init__(coordinator)
        self.config_entry = config_entry
        self.lock_data = lock_data
        self.lock_id = lock_data["lockId"]

    @property
    def available(self):
        """Return avalibility"""
        return self.lock_data is not None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.lock_id in self.coordinator.data:
            self.lock_data = self.coordinator.data[self.lock_id]
        self.async_write_ha_state()

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, self.lock_id),
                (DOMAIN, self.lock_data["lockMac"]),
            },
            "name": self.lock_data["lockName"],
            # "model": VERSION,
            # "manufacturer": NAME,
        }
