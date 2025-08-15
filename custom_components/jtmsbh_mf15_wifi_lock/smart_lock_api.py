"""Smart Lock API Bridge for JTMSBH WiFi Lock integration.

This module provides independent API access to smart-lock specific endpoints
using tuya-connector-python for direct authentication with Tuya OpenAPI.
"""
from __future__ import annotations

import logging
from typing import Any
import json

# Try to import from tuya-connector-python
try:
    from tuya_connector import TuyaOpenAPI
    TUYA_CONNECTOR_AVAILABLE = True
except ImportError:
    TUYA_CONNECTOR_AVAILABLE = False
    TuyaOpenAPI = None

_LOGGER = logging.getLogger(__name__)


class SmartLockApiClient:
    """API client for smart-lock specific endpoints using tuya-connector-python."""

    def __init__(self, _device_manager, device_id: str, access_id: str, access_secret: str) -> None:
        """Initialize the smart lock API client.

        Args:
            _device_manager: The Manager instance from tuya_sharing (unused in new approach)
            device_id: The device ID for the smart lock
            access_id: Tuya IoT Platform Access ID/Client ID
            access_secret: Tuya IoT Platform Access Secret/Client Secret
        """
        self.device_id = device_id
        self.access_id = access_id
        self.access_secret = access_secret

        # Smart lock API endpoints
        self.ticket_url = f"/v1.0/devices/{device_id}/door-lock/password-ticket"
        self.operate_url = f"/v1.0/smart-lock/devices/{device_id}/password-free/door-operate"

        # Initialize TuyaOpenAPI if available
        self.tuya_open_api = None

        if TUYA_CONNECTOR_AVAILABLE:
            _LOGGER.debug("Tuya-connector-python is available - initializing independent API client")
            self._initialize_tuya_connector()
        else:
            _LOGGER.debug("Tuya-connector-python not available. Install with: pip install tuya-connector-python")

    def _initialize_tuya_connector(self):
        """Initialize TuyaOpenAPI using tuya-connector-python with credentials from config."""
        try:
            _LOGGER.debug("Initializing Tuya connector for device %s", self.device_id)

            # Initialize TuyaOpenAPI with independent credentials
            if TuyaOpenAPI is not None:
                # Try both API endpoints - US first since user is US-based
                api_endpoints_to_try = [
                    ("https://openapi.tuyaus.com", "US"),
                    ("https://openapi.tuyacn.com", "China"),
                ]

                api_initialized = False
                for api_endpoint, region in api_endpoints_to_try:
                    try:
                        _LOGGER.debug("Trying API endpoint: %s (%s)", api_endpoint, region)
                        self.tuya_open_api = TuyaOpenAPI(
                            endpoint=api_endpoint,
                            access_id=self.access_id,
                            access_secret=self.access_secret,
                            lang="en"
                        )

                        # Just initialize - will test connection during first API call
                        _LOGGER.debug("TuyaOpenAPI initialized with %s endpoint", region)
                        api_initialized = True
                        break
                    except Exception as e:
                        _LOGGER.debug("Failed to initialize API with %s endpoint: %s", region, e)
                        self.tuya_open_api = None

                if not api_initialized:
                    _LOGGER.error("Failed to initialize API with any endpoint")
                    self.tuya_open_api = None
                    return

                _LOGGER.debug("TuyaOpenAPI initialized successfully")
            else:
                _LOGGER.debug("TuyaOpenAPI class is None")
                self.tuya_open_api = None

        except Exception as e:
            _LOGGER.error("Failed to initialize TuyaOpenAPI: %s", e)
            self.tuya_open_api = None

    def _post_request(self, url: str, body: dict | None = None) -> dict[str, Any]:
        """Make smart lock API request using TuyaOpenAPI."""
        if self.tuya_open_api is None:
            return {
                "success": False,
                "message": "TuyaOpenAPI not initialized. Check credentials configuration",
                "error": "No API client available"
            }

        try:
            _LOGGER.debug("Making TuyaOpenAPI request to: %s", url)
            _LOGGER.debug("Request body: %s", json.dumps(body or {}, indent=2))

            # Use TuyaOpenAPI's post method - it handles all signing automatically
            response = self.tuya_open_api.post(url, body)

            _LOGGER.debug("TuyaOpenAPI Response: %s", json.dumps(response, indent=2))

            # Enhanced error handling for authentication failures
            if isinstance(response, dict):
                error_code = response.get('code')
                error_msg = response.get('msg', '')

                if error_code == 1004:
                    _LOGGER.error("Authentication signature invalid (code 1004). Check your Tuya IoT Platform credentials")

                    return {
                        "success": False,
                        "message": f"Authentication failed: {error_msg}. Check credentials configuration",
                        "error": f"API returned code {error_code}: {error_msg}",
                        "code": error_code
                    }
                elif error_code == 1010:
                    _LOGGER.debug("Token expired (code 1010), attempting automatic refresh")
                    # tuya-connector-python should handle token refresh automatically
                    # Let's try the request one more time after a brief delay
                    import time
                    time.sleep(1)  # Brief delay to allow token refresh

                    # Retry the request once
                    _LOGGER.debug("Retrying request after token refresh")
                    retry_response = self.tuya_open_api.post(url, body)
                    _LOGGER.debug("Retry response: %s", json.dumps(retry_response, indent=2))

                    # If retry still fails, return the error
                    if isinstance(retry_response, dict) and retry_response.get('code') == 1010:
                        return {
                            "success": False,
                            "message": "Access token expired and refresh failed",
                            "error": f"API returned code {error_code}: {error_msg}",
                            "code": error_code
                        }

                    # Return the retry response if it succeeded or failed with different error
                    return retry_response
                elif error_code and error_code != 200:
                    _LOGGER.debug("API error (code %s): %s", error_code, error_msg)
                    return {
                        "success": False,
                        "message": f"API error: {error_msg}",
                        "error": f"API returned code {error_code}: {error_msg}",
                        "code": error_code
                    }

            return response

        except Exception as e:
            _LOGGER.debug("TuyaOpenAPI request failed: %s", e)
            return {
                "success": False,
                "message": f"TuyaOpenAPI request failed: {e}",
                "error": str(e)
            }

    def unlock(self) -> bool:
        """Unlock the smart lock using the two-step API process.

        Returns:
            bool: True if unlock succeeded, False otherwise
        """
        _LOGGER.debug("Unlocking device %s", self.device_id)

        try:
            # Step 1: Get password ticket
            ticket_response = self._post_request(self.ticket_url)
            _LOGGER.debug("Ticket response: %s", json.dumps(ticket_response, indent=2, ensure_ascii=False))

            if not ticket_response.get("success", False):
                raise Exception(f"Ticket request failed: {ticket_response}")

            result = ticket_response.get("result", {})
            ticket_id = result.get("ticket_id")

            if not ticket_id:
                raise Exception(f"No ticket_id in response: {ticket_response}")

            # Step 2: Use ticket to unlock
            unlock_body = {"ticket_id": ticket_id, "open": True}
            unlock_response = self._post_request(self.operate_url, unlock_body)
            _LOGGER.debug("Unlock response: %s", json.dumps(unlock_response, indent=2, ensure_ascii=False))

            # Check for API success and operation result
            if unlock_response.get("success") and unlock_response.get("result"):
                _LOGGER.debug("Device %s unlock API succeeded", self.device_id)
                return True
            else:
                _LOGGER.debug("Device %s unlock failed or returned false result", self.device_id)
                return False

        except Exception as e:
            _LOGGER.debug("Failed to unlock device %s: %s", self.device_id, e)
            return False

    def lock(self) -> bool:
        """Lock the smart lock using the two-step API process.

        Returns:
            bool: True if lock succeeded, False otherwise
        """
        _LOGGER.debug("Locking device %s", self.device_id)

        try:
            # Step 1: Get password ticket
            ticket_response = self._post_request(self.ticket_url)
            _LOGGER.debug("Ticket response: %s", json.dumps(ticket_response, indent=2, ensure_ascii=False))

            if not ticket_response.get("success", False):
                raise Exception(f"Ticket request failed: {ticket_response}")

            result = ticket_response.get("result", {})
            ticket_id = result.get("ticket_id")

            if not ticket_id:
                raise Exception(f"No ticket_id in response: {ticket_response}")

            # Step 2: Use ticket to lock
            lock_body = {"ticket_id": ticket_id, "open": False}
            lock_response = self._post_request(self.operate_url, lock_body)
            _LOGGER.debug("Lock response: %s", json.dumps(lock_response, indent=2, ensure_ascii=False))

            # Check for API success and operation result
            if lock_response.get("success") and lock_response.get("result"):
                _LOGGER.debug("Device %s lock API succeeded", self.device_id)
                return True
            else:
                _LOGGER.debug("Device %s lock failed or returned false result", self.device_id)
                return False

        except Exception as e:
            _LOGGER.debug("Failed to lock device %s: %s", self.device_id, e)
            return False

    def get_device_status(self, verbose_logging: bool = True) -> dict[str, Any] | None:
        """Get current device status using Tuya OpenAPI.

        Args:
            verbose_logging: If True, logs full response data. If False, only logs relevant lock state info.

        Returns:
            dict: Device status data if successful, None otherwise
        """
        if self.tuya_open_api is None:
            _LOGGER.debug("TuyaOpenAPI not initialized for status request")
            return None

        try:
            # Use standard device status endpoint
            status_url = f"/v1.0/devices/{self.device_id}/status"
            if verbose_logging:
                _LOGGER.debug("Getting device status from: %s", status_url)

            response = self.tuya_open_api.get(status_url)
            if verbose_logging:
                _LOGGER.debug("Status response: %s", json.dumps(response, indent=2))

            if isinstance(response, dict) and response.get("success", False):
                result = response.get("result", [])

                # Convert status list to dictionary for easier access
                status_dict = {}
                for item in result:
                    if isinstance(item, dict) and "code" in item and "value" in item:
                        status_dict[item["code"]] = item["value"]

                if verbose_logging:
                    _LOGGER.debug("Parsed status dict: %s", status_dict)
                else:
                    # Only log the lock motor state during routine polling
                    lock_state = status_dict.get("lock_motor_state")
                    if lock_state is not None:
                        _LOGGER.debug("Lock motor state: %s", lock_state)
                
                return status_dict
            else:
                error_code = response.get('code') if isinstance(response, dict) else 'unknown'
                error_msg = response.get('msg', 'Unknown error') if isinstance(response, dict) else str(response)
                _LOGGER.debug("Status API error (code %s): %s", error_code, error_msg)
                return None

        except Exception as e:
            _LOGGER.debug("Failed to get device status for %s: %s", self.device_id, e)
            return None

    def get_device_status_verbose(self) -> dict[str, Any] | None:
        """Get current device status with verbose logging for troubleshooting.
        
        This method always uses verbose logging and is intended for initial setup,
        troubleshooting, or when detailed response information is needed.
        
        Returns:
            dict: Device status data if successful, None otherwise
        """
        return self.get_device_status(verbose_logging=True)

