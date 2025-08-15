"""TinyTuya real-time monitoring for JTMSBH lock devices."""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections.abc import Callable

_LOGGER = logging.getLogger(__name__)

try:
    import tinytuya
    TINYTUYA_AVAILABLE = True
except ImportError:
    TINYTUYA_AVAILABLE = False
    tinytuya = None


class TinyTuyaMonitor:
    """Monitor Tuya device using TinyTuya for real-time updates."""

    def __init__(self, device_id: str, access_id: str, access_secret: str) -> None:
        """Initialize TinyTuya monitor."""
        self.device_id = device_id
        self.access_id = access_id
        self.access_secret = access_secret
        self.cloud = None
        self.device = None
        self._listeners: list[Callable[[str, dict], None]] = []
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._running = False
        self._lan_available = False
        self._device_ip = None
        self._local_key = None
        self._last_lock_state = None
        self._fast_polling_until = 0  # Timestamp when to stop fast polling
        self._fast_polling_lock = threading.Lock()

    def add_listener(self, callback: Callable[[str, dict], None]) -> None:
        """Add a callback for device updates."""
        self._listeners.append(callback)
        _LOGGER.debug("Added TinyTuya listener for device %s", self.device_id)

    def remove_listener(self, callback: Callable[[str, dict], None]) -> None:
        """Remove a callback for device updates."""
        if callback in self._listeners:
            self._listeners.remove(callback)
            _LOGGER.debug("Removed TinyTuya listener for device %s", self.device_id)

    async def async_start(self) -> bool:
        """Start the TinyTuya monitor."""
        if not TINYTUYA_AVAILABLE:
            _LOGGER.debug("TinyTuya not available for device %s", self.device_id)
            return False

        try:
            # Initialize cloud connection in executor to avoid blocking
            def _initialize_cloud():
                if tinytuya is None:
                    return None, "TinyTuya not available"

                cloud = tinytuya.Cloud(
                    apiRegion="us",  # or "cn", "eu", "in" depending on your region
                    apiKey=self.access_id,
                    apiSecret=self.access_secret,
                    apiDeviceID=self.device_id
                )

                # Test cloud connection
                result = cloud.getconnectstatus()
                if not result:
                    return None, "Connection test failed"

                # Get device info
                device_info = cloud.getdevices()
                if not device_info:
                    return None, "Device not found"

                # Try to find our specific device for LAN connection
                try:
                    device_data = None
                    if isinstance(device_info, list):
                        for device in device_info:
                            if isinstance(device, dict) and device.get('id') == self.device_id:
                                device_data = device
                                break

                    if device_data:
                        device_ip = device_data.get('ip')
                        local_key = device_data.get('local_key')

                        if device_ip and local_key:
                            _LOGGER.debug("TinyTuya found device IP (%s) and local key for LAN connection", device_ip)
                            return cloud, f"Success with LAN: {device_ip}"
                        else:
                            _LOGGER.debug("TinyTuya device missing IP or local key, using cloud polling")
                            return cloud, "Success cloud polling"
                    else:
                        _LOGGER.debug("TinyTuya could not find device, using cloud polling")
                        return cloud, "Success cloud polling"
                except Exception as lan_error:
                    _LOGGER.debug("TinyTuya LAN setup failed: %s, using cloud polling", lan_error)
                    return cloud, "Success cloud polling"

            # Run initialization in executor
            cloud_result = await asyncio.get_event_loop().run_in_executor(
                None, _initialize_cloud
            )

            self.cloud, status_message = cloud_result

            if not self.cloud:
                _LOGGER.warning("TinyTuya initialization failed for device %s: %s", self.device_id, status_message)
                return False

            _LOGGER.debug("TinyTuya cloud connection established for device %s", self.device_id)

            # Check if we can use LAN connection for local polling priority
            self._lan_available = "LAN:" in status_message
            if self._lan_available:
                self._device_ip = status_message.split("LAN: ")[1]
                device_info = self.cloud.getdevices()
                if device_info and isinstance(device_info, list):
                    for device in device_info:
                        if isinstance(device, dict) and device.get('id') == self.device_id:
                            self._local_key = device.get('local_key')
                            break

            # Start monitoring thread (either subscription-based or polling-based)
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True
            )
            self._monitor_thread.start()
            self._running = True

            if self._lan_available:
                _LOGGER.debug("TinyTuya LAN real-time monitor started for device %s (IP: %s)", self.device_id, self._device_ip)
            else:
                _LOGGER.debug("TinyTuya cloud polling monitor started for device %s", self.device_id)
            return True

        except Exception as e:
            _LOGGER.error("Failed to start TinyTuya monitor for device %s: %s", self.device_id, e)
            return False


    def _monitor_loop(self) -> None:
        """Monitor device status in background thread."""
        _LOGGER.debug("TinyTuya monitoring loop started for device %s", self.device_id)

        # Try LAN connection first for local polling priority
        if self._lan_available and self._device_ip and self._local_key:
            try:
                if tinytuya is None:
                    _LOGGER.debug("TinyTuya not available for LAN connection")
                    self._monitor_device(self.cloud, is_lan=False)
                    return

                lan_device = tinytuya.Device(
                    dev_id=self.device_id,
                    address=self._device_ip,
                    local_key=self._local_key,
                    version=3.3
                )

                # Test LAN connection
                if lan_device.status() and 'dps' in lan_device.status():
                    _LOGGER.debug("TinyTuya LAN connection established for device %s", self.device_id)
                    self._monitor_device(lan_device, is_lan=True)
                    return

            except Exception as e:
                _LOGGER.debug("TinyTuya LAN setup failed for device %s: %s, using cloud polling", self.device_id, e)

        # Fallback to cloud polling
        _LOGGER.debug("Using TinyTuya cloud polling for device %s", self.device_id)
        self._monitor_device(self.cloud, is_lan=False)

    def _monitor_device(self, device, is_lan: bool) -> None:
        """Monitor device with adaptive polling logic."""
        # Passive monitoring intervals
        passive_interval = 5 if is_lan else 10
        # Fast polling intervals (after HA state change)
        fast_interval = 1 if is_lan else 2

        last_poll = 0

        while not self._stop_event.is_set():
            try:
                current_time = time.time()

                # Determine current polling interval based on fast polling state
                with self._fast_polling_lock:
                    is_fast_polling = current_time < self._fast_polling_until

                poll_interval = fast_interval if is_fast_polling else passive_interval

                if current_time >= last_poll:
                    current_lock_state = self._get_lock_state(device, is_lan)

                    if current_lock_state is not None and current_lock_state != self._last_lock_state:
                        mode = "fast" if is_fast_polling else "passive"
                        _LOGGER.debug("TinyTuya %s detected device %s lock state change (%s): %s -> %s",
                                   "LAN" if is_lan else "cloud", self.device_id, mode,
                                   self._last_lock_state, current_lock_state)

                        status_dict = {'lock_motor_state': current_lock_state}
                        self._notify_listeners(status_dict)
                        self._last_lock_state = current_lock_state

                    last_poll = current_time + poll_interval

                # Sleep for shorter duration when fast polling
                sleep_time = 0.5 if is_fast_polling else 1
                time.sleep(sleep_time)

            except Exception as e:
                _LOGGER.debug("TinyTuya %s polling error for device %s: %s",
                           "LAN" if is_lan else "cloud", self.device_id, e)
                time.sleep(5)

    def _get_lock_state(self, device, is_lan: bool):
        """Extract lock state from device status."""
        try:
            if is_lan:
                status = device.status()
                return status.get('dps', {}).get('1') if status else None
            else:
                status = device.getstatus(self.device_id)
                if isinstance(status, dict) and 'result' in status:
                    for item in status.get('result', []):
                        if isinstance(item, dict) and item.get('code') == 'lock_motor_state':
                            return item.get('value')
                return None
        except Exception:
            return None

    def _notify_listeners(self, status_dict: dict) -> None:
        """Notify all listeners of status change."""
        for callback in self._listeners:
            try:
                callback(self.device_id, status_dict)
            except Exception as e:
                _LOGGER.error("Error in TinyTuya callback for device %s: %s", self.device_id, e)

        _LOGGER.debug("TinyTuya monitoring stopped for device %s", self.device_id)

    def enable_fast_polling(self, duration: int = 30) -> None:
        """Enable fast polling for specified duration after HA state change.

        Args:
            duration: Duration in seconds to maintain fast polling (default 30s)
        """
        with self._fast_polling_lock:
            self._fast_polling_until = time.time() + duration
            _LOGGER.debug("Enabled fast polling for device %s for %ds", self.device_id, duration)

    async def async_stop(self) -> None:
        """Stop the TinyTuya monitor."""
        if self._running:
            _LOGGER.debug("Stopping TinyTuya monitor for device %s", self.device_id)
            self._stop_event.set()

            if self._monitor_thread and self._monitor_thread.is_alive():
                await asyncio.get_event_loop().run_in_executor(
                    None, self._monitor_thread.join, 5
                )

            self._running = False
            _LOGGER.debug("TinyTuya monitor stopped for device %s", self.device_id)

    @property
    def is_running(self) -> bool:
        """Return True if monitor is running."""
        return self._running