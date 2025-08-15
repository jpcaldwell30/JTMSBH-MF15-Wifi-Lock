"""Constants for the JTMSBH MF15 Wifi Lock integration."""
from __future__ import annotations

import logging
from enum import StrEnum

from homeassistant.const import Platform

DOMAIN = "jtmsbh_mf15_wifi_lock"
TUYA_DOMAIN = "tuya"  # Reference to core Tuya integration
LOGGER = logging.getLogger(__package__)

# Configuration keys
CONF_ACCESS_ID = "access_id"
CONF_ACCESS_SECRET = "access_secret"

# Discovery signal for JTMSBH devices
JTMSBH_DISCOVERY_NEW = "jtmsbh_discovery_new"

PLATFORMS = [
    Platform.LOCK,
    Platform.SENSOR,
]


class DPCode(StrEnum):
    """Data Point Codes used by JTMSBH MF15 Lock.
    
    https://developer.tuya.com/en/docs/iot/standarddescription?id=K9i5ql6waswzq
    """
    M15_WIFI_01_LOCK_STATE = "lock_motor_state"
    M15_WIFI_01_BATTERY_PERCENTAGE = "residual_electricity"