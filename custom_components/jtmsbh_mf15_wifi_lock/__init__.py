"""Support for JTMSBH MF15 Wifi Lock extending Tuya integration."""
from __future__ import annotations

import logging
from typing import NamedTuple

from homeassistant.config_entries import ConfigEntry
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, Event, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED

from .const import DOMAIN, PLATFORMS, TUYA_DOMAIN, JTMSBH_DISCOVERY_NEW, CONF_ACCESS_ID, CONF_ACCESS_SECRET
from .tuya_helper import get_jtmsbh_devices, is_tuya_integration_available, get_tuya_device_manager
# Services removed per user request - debugging will be done via command line
_LOGGER = logging.getLogger(__name__)


class JTMSBHData(NamedTuple):
    """JTMSBH data stored in the Home Assistant data object."""

    monitored_devices: set[str]
    access_id: str
    access_secret: str


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up JTMSBH MF15 Lock from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Handle migration from old config entries without API credentials
    if CONF_ACCESS_ID not in entry.data or CONF_ACCESS_SECRET not in entry.data:
        _LOGGER.warning(
            "Config entry missing API credentials. Smart Lock API and TinyTuya features "
            "will be disabled. Please reconfigure the integration to add your Tuya IoT "
            "Platform Access ID and Access Secret for full functionality"
        )
        # Use empty credentials as fallback - entities will handle gracefully
        access_id = ""
        access_secret = ""
    else:
        access_id = entry.data[CONF_ACCESS_ID]
        access_secret = entry.data[CONF_ACCESS_SECRET]

    # Initialize our data storage
    hass.data[DOMAIN][entry.entry_id] = JTMSBHData(
        monitored_devices=set(),
        access_id=access_id,
        access_secret=access_secret,
    )

    # Services removed per user request - debugging will be done via command line

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Start monitoring for Tuya devices after Home Assistant has started
    if hass.is_running:
        await _async_setup_tuya_monitoring(hass, entry)
    else:
        async def _on_ha_started(event: Event) -> None:
            await _async_setup_tuya_monitoring(hass, entry)

        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED,
            _on_ha_started
        )

    return True


async def _async_setup_tuya_monitoring(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up monitoring of Tuya integration devices."""
    # Check if Tuya integration is loaded
    if not is_tuya_integration_available(hass):
        _LOGGER.warning("Tuya integration not found or not loaded. JTMSBH lock integration requires Tuya integration to be set up first")
        return

    # Find existing JTMSBH devices in Tuya integration
    await _discover_existing_devices(hass, entry)

    # Set up listeners for new devices
    _setup_device_listeners(hass, entry)


async def _discover_existing_devices(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Discover existing JTMSBH devices from Tuya integration."""
    jtmsbh_data = hass.data[DOMAIN][entry.entry_id]
    discovered_devices = []

    # Get all JTMSBH devices from Tuya integrations
    jtmsbh_devices = get_jtmsbh_devices(hass)

    for device_manager, device in jtmsbh_devices:
        if device.id not in jtmsbh_data.monitored_devices:
            _LOGGER.debug("Found JTMSBH device: %s (%s)", device.name, device.id)
            discovered_devices.append(device.id)
            jtmsbh_data.monitored_devices.add(device.id)

            # Update the device registry to show as supported JTMSBH device
            await _update_device_registry(hass, device)

    if discovered_devices:
        async_dispatcher_send(hass, JTMSBH_DISCOVERY_NEW, discovered_devices)


async def _update_device_registry(hass: HomeAssistant, device) -> None:
    """Update device registry to show JTMSBH device as supported."""
    device_registry = dr.async_get(hass)

    # Find the existing device entry
    device_entry = device_registry.async_get_device(identifiers={(TUYA_DOMAIN, device.id)})

    if device_entry:
        # Update the device to show it's now supported
        device_registry.async_update_device(
            device_entry.id,
            model=f"JTMSBH {device.product_name}",  # Remove "(unsupported)" and add JTMSBH prefix
            name=device.name,  # Use the actual device name instead of technical ID
        )
        _LOGGER.debug("Updated device registry for JTMSBH device: %s", device.name)


def _setup_device_listeners(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up listeners for new Tuya devices."""
    jtmsbh_data = hass.data[DOMAIN][entry.entry_id]

    @callback
    def handle_tuya_discovery(event: Event) -> None:
        """Handle discovery of new Tuya devices."""
        if event.data.get("domain") != TUYA_DOMAIN:
            return

        # Get the Tuya device manager from the event or data
        # This is a simplified approach - you might need to adjust based on
        # how the core Tuya integration exposes device discovery events
        pass

    # Note: The core Tuya integration doesn't expose a clean discovery event
    # This is a limitation of extending vs replacing. In practice, you might need
    # to periodically check for new devices or hook into the device registry changes.

    # Alternative approach: Monitor device registry changes
    @callback
    async def handle_device_registry_update(event: Event) -> None:
        """Handle device registry updates to detect new Tuya devices."""
        action = event.data.get("action")
        device_id = event.data.get("device_id")

        if action != "create":
            return

        device_registry = dr.async_get(hass)
        if device_id is None:
            return
        device_entry = device_registry.async_get(device_id)

        if not device_entry:
            return

        # Check if this is a Tuya device
        tuya_identifier = None
        for identifier in device_entry.identifiers:
            if identifier[0] == TUYA_DOMAIN:
                tuya_identifier = identifier[1]
                break

        if not tuya_identifier:
            return

        # Check if we can find this device in any Tuya integration data
        device_manager, device = get_tuya_device_manager(hass, tuya_identifier)

        if device and device.category == 'jtmsbh' and device.id not in jtmsbh_data.monitored_devices:
            _LOGGER.debug("New JTMSBH device detected: %s (%s)", device.name, device.id)
            jtmsbh_data.monitored_devices.add(device.id)
            # Update device registry for new device
            await _update_device_registry(hass, device)
            async_dispatcher_send(hass, JTMSBH_DISCOVERY_NEW, [device.id])

    # Listen for device registry updates
    hass.bus.async_listen("device_registry_updated", handle_device_registry_update)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload_ok