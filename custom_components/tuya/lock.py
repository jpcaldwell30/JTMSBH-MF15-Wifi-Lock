"""Support for Tuya Locks"""
from __future__ import annotations
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.const import PERCENTAGE
from homeassistant.components.lock import LockEntity, LockEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from tuya_iot import TuyaDevice, TuyaDeviceManager


_LOGGER = logging.getLogger(__name__)

from . import HomeAssistantTuyaData
from .base import TuyaEntity
from .const import DOMAIN, TUYA_DISCOVERY_NEW, DPCode

@dataclass
class TuyaLockEntityDescription(LockEntityDescription):
    unlocked_value: bool = True
    locked_value: bool = False

# standard is defined as Send: 1 byte. true: unlocks the door. false: locks the door.
# Report: 1 byte. true: indicates the unlocked status. false: indicates the locked status.

LOCKS: dict[str, TuyaLockEntityDescription] = {
    # "<lock catagory>":
    #     TuyaLockEntityDescription(
    #         key=<DPcode.YOUR_LOCKS_DP_CODE_YOU_DEFINED_FOR_THE_LOCK_STATE_IN_CONST.PY>,
    #         icon="mdi:lock",
    #     ),
    "jtmsbh":
        TuyaLockEntityDescription(
            key=DPCode.M15_WIFI_01_LOCK_STATE,
            icon="mdi:lock",
        ),
}

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up tuya lock dynamically through tuya discovery."""
    hass_data: HomeAssistantTuyaData = hass.data[DOMAIN][entry.entry_id]

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add a discovered tuya lock."""
        entities: list[TuyaLockEntity] = []
        for device_id in device_ids:
            device = hass_data.device_manager.device_map[device_id]
            if description := LOCKS.get(device.category):
                entities.append(TuyaLockEntity(device, hass_data.device_manager, description))

        async_add_entities(entities)

    async_discover_device([*hass_data.device_manager.device_map])

    entry.async_on_unload(
        async_dispatcher_connect(hass, TUYA_DISCOVERY_NEW, async_discover_device)
    )

class TuyaLockEntity(TuyaEntity, LockEntity):
  """Tuya Lock Device."""
  _closed_opened_dpcode: DPCode | None = None
  entity_description: TuyaLockEntityDescription | None = None

  def __init__(
      self,
      device: TuyaDevice,
      device_manager: TuyaDeviceManager,
      description: TuyaLockEntityDescription,
  ) -> None:
    """Init TuyaHaLock."""
    super().__init__(device, device_manager)
    self.ticket_url = "/v1.0/smart-lock/devices/" + self.device.id + "/password-ticket"
    self.operate_url = "/v1.0/smart-lock/devices/"+ self.device.id + "/password-free/door-operate"
    self.entity_description = description

    # Find the DPCode for the lock state.
    self._closed_opened_dpcode = DPCode.M15_WIFI_01_LOCK_STATE

  @property
  def is_locked(self) -> bool | None:
    """Return true if the lock is locked."""
    # Get the status of the lock.
    _LOGGER.debug("closed open dpcode is %s", self._closed_opened_dpcode)
    status = self.device.status.get(self._closed_opened_dpcode)
    _LOGGER.debug("status is %s", status)

    # If the status is None, return None.
    if status is None:
      return None

    # Return True if the status is equal to the locked_value property of the entity_description object, False otherwise.
    return status == self.entity_description.locked_value
  
  def lock(self, **kwargs):
    """Lock the lock."""
    ticket_response = self.device_manager.api.post(self.ticket_url)
    ticket_id = ticket_response["result"].get("ticket_id")
    body = {
    "ticket_id":ticket_id,
    "open":False
    }
    self.device_manager.api.post(self.operate_url, body)

  def unlock(self, **kwargs):
    """Unlock the lock."""
    ticket_response = self.device_manager.api.post(self.ticket_url)
    ticket_id = ticket_response["result"].get("ticket_id")
    body = {
    "ticket_id":ticket_id,
    "open":True
    }
    self.device_manager.api.post(self.operate_url, body)