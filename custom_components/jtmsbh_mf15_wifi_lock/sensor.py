"""Support for JTMSBH MF15 Wifi Lock sensors extending Tuya integration."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN, TUYA_DOMAIN, JTMSBH_DISCOVERY_NEW, DPCode
from .tuya_helper import get_tuya_device_manager


@dataclass(frozen=True)
class JTMSBHSensorEntityDescription(SensorEntityDescription):
    """Describes JTMSBH sensor entity."""
    pass


SENSORS: dict[str, tuple[JTMSBHSensorEntityDescription, ...]] = {
    "jtmsbh": (
        JTMSBHSensorEntityDescription(
            key=DPCode.M15_WIFI_01_BATTERY_PERCENTAGE,
            translation_key="battery",
            device_class=SensorDeviceClass.BATTERY,
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:battery-lock",
        ),
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up JTMSBH sensor entities."""

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add JTMSBH sensor entities."""
        entities: list[JTMSBHSensorEntity] = []

        for device_id in device_ids:
            # Get device manager and device from Tuya integration
            device_manager, device = get_tuya_device_manager(hass, device_id)

            if device_manager and device and device.category == 'jtmsbh':
                if descriptions := SENSORS.get(device.category):
                    for description in descriptions:
                        if description.key in device.status:
                            entities.append(
                                JTMSBHSensorEntity(device, device_manager, description)
                            )

        if entities:
            async_add_entities(entities)

    # Discover any existing devices
    jtmsbh_data = hass.data[DOMAIN][entry.entry_id]
    if jtmsbh_data.monitored_devices:
        async_discover_device(list(jtmsbh_data.monitored_devices))

    # Listen for new device discoveries
    entry.async_on_unload(
        async_dispatcher_connect(hass, JTMSBH_DISCOVERY_NEW, async_discover_device)
    )


class JTMSBHSensorEntity(SensorEntity):
    """JTMSBH Sensor Entity that extends Tuya devices."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        device,
        device_manager,
        description: JTMSBHSensorEntityDescription,
    ) -> None:
        """Initialize the JTMSBH sensor entity."""
        self.device = device
        self.device_manager = device_manager
        self.entity_description = description

        # Set unique ID
        self._attr_unique_id = f"{device.id}_{description.key}"

        # Set device info to link with existing Tuya device
        self._attr_device_info = {
            "identifiers": {(TUYA_DOMAIN, device.id)},
        }

    @property
    def available(self) -> bool:
        """Return if the device is available."""
        return self.device.online


    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        value = self.device.status.get(self.entity_description.key)
        return value

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        # Set up listener for device updates from Tuya integration
        @callback
        def handle_tuya_update() -> None:
            """Handle updates from Tuya integration."""
            self.async_write_ha_state()

        # Listen for updates to this specific device
        signal = f"tuya_entry_update_{self.device.id}"
        self.async_on_remove(
            async_dispatcher_connect(self.hass, signal, handle_tuya_update)
        )