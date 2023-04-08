"""Sensor platform for TTLock."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass

from .const import (
    DOMAIN,
)
from .entity import TTLockEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    for lock_data in coordinator.data["locks"].values():
        async_add_devices([TTLockBatterySensor(coordinator, entry, lock_data)])


class TTLockBatterySensor(TTLockEntity, SensorEntity):
    """integration_blueprint binary_sensor class."""

    def __init__(self, coordinator, config_entry, lock_data):
        super().__init__(coordinator, config_entry, lock_data)
        self.lock_state = 2

    @property
    def name(self):
        """Return the name of the lock."""
        return self.lock_data["lockAlias"] + " Battery"

    @property
    def device_class(self):
        return SensorDeviceClass.BATTERY

    @property
    def native_value(self):
        return int(self.lock_data["electricQuantity"])

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return str(self.lock_id) + "_battery"
