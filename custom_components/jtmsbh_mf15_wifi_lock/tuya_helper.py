"""Helper functions to access the core Tuya integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .const import TUYA_DOMAIN

_LOGGER = logging.getLogger(__name__)


def get_tuya_device_manager(hass: HomeAssistant, device_id: str) -> tuple[Any, Any] | tuple[None, None]:
    """Get the Tuya device manager and device for a given device ID.
    
    Returns:
        Tuple of (device_manager, device) or (None, None) if not found
    """
    # Get all Tuya config entries
    tuya_entries = [entry for entry in hass.config_entries.async_entries(TUYA_DOMAIN)]
    
    if not tuya_entries:
        _LOGGER.warning("No Tuya integration config entries found")
        return None, None
    
    for entry in tuya_entries:
        if entry.runtime_data is None:
            continue
            
        # Access the manager from runtime_data
        device_manager = entry.runtime_data.manager
        if hasattr(device_manager, 'device_map') and device_id in device_manager.device_map:
            return device_manager, device_manager.device_map[device_id]
    
    _LOGGER.debug("Device %s not found in any Tuya device manager", device_id)
    return None, None


def get_all_tuya_devices(hass: HomeAssistant) -> list[tuple[Any, Any]]:
    """Get all devices from all Tuya integrations.
    
    Returns:
        List of (device_manager, device) tuples
    """
    devices = []
    
    # Get all Tuya config entries
    tuya_entries = [entry for entry in hass.config_entries.async_entries(TUYA_DOMAIN)]
    
    for entry in tuya_entries:
        if entry.runtime_data is None:
            continue
            
        # Access the manager from runtime_data
        device_manager = entry.runtime_data.manager
        if hasattr(device_manager, 'device_map'):
            for device in device_manager.device_map.values():
                devices.append((device_manager, device))
    
    return devices


def is_tuya_integration_available(hass: HomeAssistant) -> bool:
    """Check if Tuya integration is available and loaded."""
    # Get all Tuya config entries
    tuya_entries = [entry for entry in hass.config_entries.async_entries(TUYA_DOMAIN)]
    
    # Check if there's at least one loaded Tuya integration with runtime_data
    for entry in tuya_entries:
        if entry.runtime_data is not None and hasattr(entry.runtime_data, 'manager'):
            return True
    
    return False


def get_jtmsbh_devices(hass: HomeAssistant) -> list[tuple[Any, Any]]:
    """Get all JTMSBH devices from Tuya integrations.
    
    Returns:
        List of (device_manager, device) tuples for JTMSBH devices
    """
    jtmsbh_devices = []
    
    all_devices = get_all_tuya_devices(hass)
    for device_manager, device in all_devices:
        if hasattr(device, 'category') and device.category == 'jtmsbh':
            jtmsbh_devices.append((device_manager, device))
    
    return jtmsbh_devices