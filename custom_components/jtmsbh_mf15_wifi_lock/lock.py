"""Support for JTMSBH MF15 Wifi Locks extending Tuya integration."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any
import asyncio
import time
import threading

from homeassistant.components.lock import LockEntity, LockEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# Component imports (placed after standard homeassistant imports)
from homeassistant.components.tuya.entity import TuyaEntity
from .const import DOMAIN, JTMSBH_DISCOVERY_NEW, DPCode
from .tuya_helper import get_tuya_device_manager
from .smart_lock_api import SmartLockApiClient
from .tinytuya_monitor import TinyTuyaMonitor

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class JTMSBHLockEntityDescription(LockEntityDescription):
    """Describes JTMSBH lock entity."""
    unlocked_value: bool = True
    locked_value: bool = False


LOCKS: dict[str, JTMSBHLockEntityDescription] = {
    "jtmsbh": JTMSBHLockEntityDescription(
        key=DPCode.M15_WIFI_01_LOCK_STATE,
        icon="mdi:lock",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up JTMSBH lock entities."""

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add JTMSBH lock entities."""
        entities: list[JTMSBHLockEntity] = []
        jtmsbh_data = hass.data[DOMAIN][entry.entry_id]

        for device_id in device_ids:
            # Get device manager and device from Tuya integration
            device_manager, device = get_tuya_device_manager(hass, device_id)

            if device_manager and device and device.category == 'jtmsbh':
                if description := LOCKS.get(device.category):
                    _LOGGER.debug("Adding JTMSBH lock entity for device: %s", device.name)
                    entities.append(
                        JTMSBHLockEntity(
                            device,
                            device_manager,
                            description,
                            jtmsbh_data.access_id,
                            jtmsbh_data.access_secret
                        )
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


class JTMSBHLockEntity(TuyaEntity, LockEntity):
    """JTMSBH Lock Entity that extends Tuya devices."""

    _attr_has_entity_name = True
    _attr_name = None  # Use device name directly without appending entity name
    _closed_opened_dpcode: DPCode | None = None
    entity_description: JTMSBHLockEntityDescription
    _fallback_polling_thread: threading.Thread | None = None
    _fallback_stop_event: threading.Event | None = None
    _fallback_running = False
    _fast_polling_until = 0  # Timestamp when to stop fast polling
    _fast_polling_lock: threading.Lock
    _last_lock_state = None

    def __init__(
        self,
        device,  # TuyaDevice from core integration
        device_manager,  # TuyaDeviceManager from core integration
        description: JTMSBHLockEntityDescription,
        access_id: str,
        access_secret: str,
    ) -> None:
        """Initialize the JTMSBH lock entity."""
        # Initialize Tuya entity base class
        super().__init__(device, device_manager)

        self.entity_description = description

        # Override unique ID to include description key
        self._attr_unique_id = f"{device.id}_{description.key}"

        # Find the DPCode for the lock state
        self._closed_opened_dpcode = DPCode.M15_WIFI_01_LOCK_STATE

        # Initialize Smart Lock API client with credentials from config
        self.smart_lock_api = SmartLockApiClient(device_manager, device.id, access_id, access_secret)

        # Initialize TinyTuya monitor for local polling priority
        self.tinytuya_monitor = TinyTuyaMonitor(
            device.id,
            access_id,
            access_secret
        )

        # Initialize fallback polling control - always create the lock
        self._fast_polling_lock = threading.Lock()
        self._fallback_stop_event = None  # Will be created when fallback starts

        _LOGGER.debug("Initialized JTMSBH lock entity for device %s", device.id)

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        await super().async_added_to_hass()

        @callback
        def _update_handler() -> None:
            """Handle device state updates via dispatcher."""
            self.async_write_ha_state()

        # Subscribe to dispatcher updates as secondary update mechanism
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"tuya_entry_update_{self.device.id}", _update_handler
            )
        )

        # Set up TinyTuya for local polling priority
        def _tinytuya_update_handler(device_id: str, status_dict: dict) -> None:
            """Handle TinyTuya updates for this device."""
            lock_state = status_dict.get('lock_motor_state')
            if lock_state is not None:
                _LOGGER.debug("TinyTuya lock state update for %s: %s", device_id, lock_state)

            # Update the device status with the new data
            for dp_code, value in status_dict.items():
                self.device.status[dp_code] = value

            # Schedule state update safely from thread
            self.hass.loop.call_soon_threadsafe(
                lambda: self.hass.async_create_task(self._async_update_from_tinytuya())
            )

        # Add TinyTuya listener and start monitoring
        self.tinytuya_monitor.add_listener(_tinytuya_update_handler)

        # Try to start TinyTuya monitor (prioritizes local LAN polling)
        tinytuya_started = await self.tinytuya_monitor.async_start()

        if tinytuya_started:
            _LOGGER.debug("TinyTuya monitoring started for device %s (local polling priority)", self.device.id)
        else:
            _LOGGER.debug("TinyTuya failed to start for device %s, starting Smart Lock API fallback polling", self.device.id)
            # Start Smart Lock API fallback polling instead of relying on Tuya integration
            await self._start_fallback_polling()


    async def _async_update_from_tinytuya(self) -> None:
        """Update entity state from TinyTuya data."""
        self.async_write_ha_state()

    async def _start_fallback_polling(self) -> None:
        """Start Smart Lock API fallback polling using TinyTuya-style timing."""
        self._fallback_stop_event = threading.Event()
        self._fallback_stop_event.clear()

        # Do initial status check with verbose logging for troubleshooting
        try:
            initial_status = await self.hass.async_add_executor_job(
                self.smart_lock_api.get_device_status_verbose
            )
            if initial_status:
                _LOGGER.debug("Initial Smart Lock API fallback status check successful for device %s", self.device.id)
            else:
                _LOGGER.debug("Initial Smart Lock API fallback status check failed for device %s", self.device.id)
        except Exception as e:
            _LOGGER.debug("Initial Smart Lock API fallback status check error for device %s: %s", self.device.id, e)

        # Start monitoring thread with TinyTuya-style logic
        self._fallback_polling_thread = threading.Thread(
            target=self._fallback_polling_loop,
            daemon=True
        )
        self._fallback_polling_thread.start()
        self._fallback_running = True

        _LOGGER.debug("Started Smart Lock API fallback polling for device %s (cloud polling mode)", self.device.id)

    def _fallback_polling_loop(self) -> None:
        """Monitor device status using Smart Lock API with adaptive polling."""
        # Cloud polling intervals (same as TinyTuya)
        passive_interval = 10  # 10 seconds passive (cloud mode)
        fast_interval = 2     # 2 seconds fast polling (cloud mode)

        last_poll = 0

        while self._fallback_stop_event is not None and not self._fallback_stop_event.is_set():
            try:
                current_time = time.time()

                # Determine current polling interval based on fast polling state
                with self._fast_polling_lock:
                    is_fast_polling = current_time < self._fast_polling_until

                poll_interval = fast_interval if is_fast_polling else passive_interval

                if current_time >= last_poll:
                    current_lock_state = self._get_lock_state_from_api()

                    if current_lock_state is not None and current_lock_state != self._last_lock_state:
                        mode = "fast" if is_fast_polling else "passive"
                        _LOGGER.debug("Smart Lock API detected device %s lock state change (%s): %s -> %s",
                                     self.device.id, mode, self._last_lock_state, current_lock_state)

                        # Update device status only if _closed_opened_dpcode is not None
                        if self._closed_opened_dpcode is not None:
                            self.device.status[self._closed_opened_dpcode] = current_lock_state
                            self._last_lock_state = current_lock_state

                            # Schedule state update safely from thread
                            self.hass.loop.call_soon_threadsafe(
                                lambda: self.hass.async_create_task(self._async_update_from_fallback())
                            )

                    last_poll = current_time + poll_interval

                # Sleep for shorter duration when fast polling
                sleep_time = 0.5 if is_fast_polling else 1
                time.sleep(sleep_time)

            except Exception as e:
                _LOGGER.debug("Smart Lock API polling error for device %s: %s", self.device.id, e)
                time.sleep(5)

    def _get_lock_state_from_api(self) -> bool | None:
        """Get current lock state using Smart Lock API.

        Note: This method uses reduced logging (verbose_logging=False) since it's called
        frequently during routine polling. For troubleshooting, use get_device_status_verbose()
        or set verbose_logging=True to see full API responses.
        """
        try:
            # Use reduced logging for routine polling to avoid log noise
            status_data = self.smart_lock_api.get_device_status(verbose_logging=False)

            if status_data and self._closed_opened_dpcode in status_data:
                return status_data[self._closed_opened_dpcode]

            return None
        except Exception as e:
            _LOGGER.debug("Failed to get lock state from API for device %s: %s", self.device.id, e)
            return None

    async def _async_update_from_fallback(self) -> None:
        """Update entity state from Smart Lock API fallback data."""
        self.async_write_ha_state()

    def enable_fallback_fast_polling(self, duration: int = 30) -> None:
        """Enable fast polling for specified duration after HA state change.

        Args:
            duration: Duration in seconds to maintain fast polling (default 30s)
        """
        if self._fallback_running:
            with self._fast_polling_lock:
                self._fast_polling_until = time.time() + duration
                _LOGGER.debug("Enabled Smart Lock API fast polling for device %s for %ds", self.device.id, duration)

    async def async_will_remove_from_hass(self) -> None:
        """Call when entity will be removed from hass."""
        # Stop fallback polling
        if self._fallback_running and self._fallback_stop_event:
            _LOGGER.debug("Stopping Smart Lock API fallback polling for device %s", self.device.id)
            self._fallback_stop_event.set()

            if self._fallback_polling_thread and self._fallback_polling_thread.is_alive():
                await asyncio.get_event_loop().run_in_executor(
                    None, self._fallback_polling_thread.join, 5
                )

            self._fallback_running = False
            _LOGGER.debug("Stopped Smart Lock API fallback polling for device %s", self.device.id)

        # Stop TinyTuya monitor
        if self.tinytuya_monitor:
            await self.tinytuya_monitor.async_stop()
            _LOGGER.debug("Stopped TinyTuya monitor for device %s", self.device.id)

        await super().async_will_remove_from_hass()

    @property
    def is_locked(self) -> bool | None:
        """Return true if the lock is locked."""
        if self._closed_opened_dpcode is None:
            return None

        status = self.device.status.get(self._closed_opened_dpcode)
        if status is None:
            return None

        return status == self.entity_description.locked_value

    async def async_lock(self, **_kwargs: Any) -> None:
        """Lock the lock."""
        # Enable fast polling to quickly detect state change
        if self.tinytuya_monitor and self.tinytuya_monitor.is_running:
            await self.hass.async_add_executor_job(self.tinytuya_monitor.enable_fast_polling, 30)
        elif self._fallback_running:
            # Enable fallback fast polling if using Smart Lock API fallback
            self.enable_fallback_fast_polling(30)

        # Use Smart Lock API for reliable command execution
        success = await self.hass.async_add_executor_job(self.smart_lock_api.lock)

        if not success:
            _LOGGER.error("Lock command failed for %s", self.device.id)
            return

        # Also send command via Tuya device manager
        try:
            await self.hass.async_add_executor_job(
                self._send_command, [{"code": self._closed_opened_dpcode, "value": self.entity_description.locked_value}]
            )
        except Exception as e:
            _LOGGER.debug("Tuya command failed for lock on %s: %s", self.device.id, e)

    async def async_unlock(self, **_kwargs: Any) -> None:
        """Unlock the lock."""
        # Enable fast polling to quickly detect state change
        if self.tinytuya_monitor and self.tinytuya_monitor.is_running:
            await self.hass.async_add_executor_job(self.tinytuya_monitor.enable_fast_polling, 30)
        elif self._fallback_running:
            # Enable fallback fast polling if using Smart Lock API fallback
            self.enable_fallback_fast_polling(30)

        # Use Smart Lock API for reliable command execution
        success = await self.hass.async_add_executor_job(self.smart_lock_api.unlock)

        if not success:
            _LOGGER.error("Unlock command failed for %s", self.device.id)
            return

        # Also send command via Tuya device manager
        try:
            await self.hass.async_add_executor_job(
                self._send_command, [{"code": self._closed_opened_dpcode, "value": self.entity_description.unlocked_value}]
            )
        except Exception as e:
            _LOGGER.debug("Tuya command failed for unlock on %s: %s", self.device.id, e)
