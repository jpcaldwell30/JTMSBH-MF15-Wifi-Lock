"""Support for Tuya Smart devices."""
from __future__ import annotations

from typing import NamedTuple
import logging
import requests
from tuya_iot import (
    AuthType,
    TuyaDevice,
    TuyaDeviceListener,
    TuyaDeviceManager,
    TuyaHomeManager,
    TuyaOpenAPI,
    TuyaOpenMQ,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import dispatcher_send

from .const import (
    CONF_ACCESS_ID,
    CONF_ACCESS_SECRET,
    CONF_APP_TYPE,
    CONF_AUTH_TYPE,
    CONF_COUNTRY_CODE,
    CONF_ENDPOINT,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
    LOGGER,
    PLATFORMS,
    TUYA_DISCOVERY_NEW,
    TUYA_HA_SIGNAL_UPDATE_ENTITY,
)

_LOGGER = logging.getLogger(__name__)


class HomeAssistantTuyaData(NamedTuple):
    """Tuya data stored in the Home Assistant data object."""

    device_listener: TuyaDeviceListener
    device_manager: TuyaDeviceManager
    home_manager: TuyaHomeManager


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Async setup hass config entry."""
    hass.data.setdefault(DOMAIN, {})
    filtered_devices = []

    auth_type = AuthType(entry.data[CONF_AUTH_TYPE])
    api = TuyaOpenAPI(
        endpoint=entry.data[CONF_ENDPOINT],
        access_id=entry.data[CONF_ACCESS_ID],
        access_secret=entry.data[CONF_ACCESS_SECRET],
        auth_type=auth_type,
    )

    api.set_dev_channel("hass")

    try:
        if auth_type == AuthType.CUSTOM:
            response = await hass.async_add_executor_job(
                api.connect, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
            )
        else:
            response = await hass.async_add_executor_job(
                api.connect,
                entry.data[CONF_USERNAME],
                entry.data[CONF_PASSWORD],
                entry.data[CONF_COUNTRY_CODE],
                entry.data[CONF_APP_TYPE],
            )
    except requests.exceptions.RequestException as err:
        raise ConfigEntryNotReady(err) from err

    if response.get("success", False) is False:
        raise ConfigEntryNotReady(response)

    tuya_mq = TuyaOpenMQ(api)
    tuya_mq.start()

    device_ids: set[str] = set()
    device_manager = TuyaDeviceManager(api, tuya_mq)
    
    for device in device_manager.device_map.values():
        _LOGGER.debug(f"device in device manager: {device.id}")
        if device.category == 'jtmsbh':
            if not any(d.id == device.id for d in filtered_devices):
                _LOGGER.debug("appending %s to dfiltered devices", device.id)
                filtered_devices.append(device)
        else:
            _LOGGER.debug(f"Skipping duplicate device with ID {device.id}")
                
    home_manager = TuyaHomeManager(api, tuya_mq, device_manager)
    listener = DeviceListener(hass, device_manager, device_ids)
    device_manager.add_device_listener(listener)

    hass.data[DOMAIN][entry.entry_id] = HomeAssistantTuyaData(
        device_listener=listener,
        device_manager=device_manager,
        home_manager=home_manager,
    )
    

    # Get devices & clean up device entities
    await hass.async_add_executor_job(home_manager.update_device_cache)
    await cleanup_device_registry(hass, device_manager, filtered_devices)


    # Register known device IDs
    device_registry = dr.async_get(hass)
    for device in device_manager.device_map.values():
        if device.category == 'jtmsbh':
            device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, device.id)},
                manufacturer="Tuya",
                name=device.name,
                model=f"{device.product_name} ({device.category})",
            )
            device_ids.add(device.id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def cleanup_device_registry(
    hass: HomeAssistant, device_manager: TuyaDeviceManager, filtered_devices: list
) -> None:
    """Remove deleted device registry entries and keep only the JTMSBH device."""
    device_registry = dr.async_get(hass)

    for device in filtered_devices:
    # Remove all devices except the JTMSBH device
        for dev_id, device_entry in list(device_registry.devices.items()):
            if device_entry.identifiers:
                identifier = next(iter(device_entry.identifiers))
                if identifier[0] == DOMAIN and identifier[1] != device.id:
                    device_registry.async_remove_device(dev_id)
                if identifier[0] == DOMAIN and identifier[1] == device.id:
                    device_registry.async_get_or_create(
                    config_entry_id=list(device_entry.config_entries)[0],
                    identifiers={(DOMAIN, device_entry.id)},
                    manufacturer="Tuya",
                    name=device.name,
                    model=f"{device.product_name} ({device.category})",
                )

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unloading the Tuya platforms."""
    unload = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload:
        hass_data: HomeAssistantTuyaData = hass.data[DOMAIN][entry.entry_id]
        hass_data.device_manager.mq.stop()
        hass_data.device_manager.remove_device_listener(hass_data.device_listener)

        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload


class DeviceListener(TuyaDeviceListener):
    """Device Update Listener."""

    def __init__(
        self,
        hass: HomeAssistant,
        device_manager: TuyaDeviceManager,
        device_ids: set[str],
    ) -> None:
        """Init DeviceListener."""
        self.hass = hass
        self.device_manager = device_manager
        self.device_ids = device_ids

    def update_device(self, device: TuyaDevice) -> None:
        """Update device status."""
        if device.id in self.device_ids:
            _LOGGER.debug(
                "Received update for device %s:",
                device.id
            )
            dispatcher_send(self.hass, f"{TUYA_HA_SIGNAL_UPDATE_ENTITY}_{device.id}")

    def add_device(self, device: TuyaDevice) -> None:
        """Add device added listener."""
        # Ensure the device isn't present stale
        self.hass.add_job(self.async_remove_device, device.id)
        _LOGGER.debug(
                "adding device %s with device category: %s",
                device.id, device.category
            )
        if device.category == 'jtmsbh':
            self.device_ids.add(device.id)
            dispatcher_send(self.hass, TUYA_DISCOVERY_NEW, [device.id])
    
            device_manager = self.device_manager
            device_manager.mq.stop()
            tuya_mq = TuyaOpenMQ(device_manager.api)
            tuya_mq.start()
    
            device_manager.mq = tuya_mq
            tuya_mq.add_message_listener(device_manager.on_message)

    def remove_device(self, device_id: str) -> None:
        """Add device removed listener."""
        self.hass.add_job(self.async_remove_device, device_id)

    @callback
    def async_remove_device(self, device_id: str) -> None:
        """Remove device from Home Assistant."""
        _LOGGER.debug("Remove device: %s", device_id)
        device_registry = dr.async_get(self.hass)
        device_entry = device_registry.async_get_device(
            identifiers={(DOMAIN, device_id)}
        )
        if device_entry is not None:
            device_registry.async_remove_device(device_entry.id)
            self.device_ids.discard(device_id)