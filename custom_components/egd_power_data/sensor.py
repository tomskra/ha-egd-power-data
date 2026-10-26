"""Sensors for EGD Power Data."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EGDPowerDataCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up consumption and production sensors."""
    coordinator: EGDPowerDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            EGDPowerDataSensor(coordinator, "ICC1", "Spotřeba", "consumption"),
            EGDPowerDataSensor(coordinator, "ISC1", "Výroba", "production"),
        ]
    )


class EGDPowerDataSensor(CoordinatorEntity[EGDPowerDataCoordinator], SensorEntity):
    """Expose one EGD profile from shared coordinator data."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(
        self,
        coordinator: EGDPowerDataCoordinator,
        profile: str,
        name: str,
        unique_suffix: str,
    ) -> None:
        super().__init__(coordinator)
        self._profile = profile
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.ean}_{unique_suffix}"

    @property
    def native_value(self) -> float | None:
        """Return the daily energy total."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data[self._profile]["value"]

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the period metadata."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data[self._profile]["attributes"]
