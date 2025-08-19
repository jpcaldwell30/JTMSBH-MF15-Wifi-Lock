# JTMSBH MF15 Wifi Lock Integration for Home Assistant

[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]
[![hacs][hacsbadge]][hacs]


A Home Assistant custom integration for JTMSBH MF15 WiFi smart locks that extends the official Tuya integration with enhanced lock support and local polling capabilities.


## PLEASE NOTE
I am having less and less time to work on this integration, so updates may be delayed. That being said, I have discovered another amazing integration which also allows bringing locks to home assistant. In all honesty is probably the best option for what this integration was trying to accomplish since it has many more features and is more robust. Please check it out here: https://github.com/azerty9971/xtend_tuya

## Features

- **Lock Entity Support**: Full lock/unlock control via Home Assistant
- **Battery Monitoring**: Battery level sensor with configurable polling
- **Enhanced Monitoring**: TinyTuya local polling for faster state updates
- **Enhanced Configuration**: Streamlined setup with validation
- **Device Discovery**: Automatic discovery of JTMSBH devices from existing Tuya integration
- **Reauth Support**: Easy credential updates when needed

## Prerequisites

This integration extends the official Home Assistant Tuya integration and requires:
1. **Lock category must be jtmsbh**: This integration will only work with locks with category "jtmsbh" when accessed through the Tuya developer portal. In practice, so far I am only aware of one lock (the lock that I have) with this category. The lock in question as previosly stated is of category "jtmsbh", but is also has the following relavent attributes. "model": "M15_WIFI_01",
"name": "SMART Lock", "productId": "26bwvzlm7ejz0ql8","productName": "SMART Lock".
2. **Tuya Integration**: The official [Tuya integration](https://www.home-assistant.io/integrations/tuya/) must be installed and configured first
3. **Device Setup**: Your JTMSBH MF15 lock must already be added to your Tuya account and visible in the Tuya integration. 
4. **Tuya IoT Platform Account**: Required for enhanced API features

## Installation

### HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations → ⋮ → Custom repositories
   - Add `https://github.com/jpcaldwell30/JTMSBH-MF15-Wifi-Lock`
   - Category: Integration
3. Search for "JTMSBH MF15 Wifi Lock" and install
4. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/jpcaldwell30/JTMSBH-MF15-Wifi-Lock/releases)
2. Copy the `custom_components/jtmsbh_mf15_wifi_lock` folder to your `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

### Step 1: Set Up Tuya Integration

Before configuring this integration, ensure you have:

1. The official Tuya integration configured and working
2. Your JTMSBH MF15 lock visible and accessible in the Tuya integration

### Step 2: Get Tuya IoT Platform Credentials

For enhanced functionality (Smart Lock API and real-time monitoring), you'll need Tuya IoT Platform credentials:

1. Go to [Tuya IoT Platform](https://iot.tuya.com/)
2. Sign in with your Tuya account
3. Click **Cloud** → **Development** → **Create Cloud Project**
4. Select **Smart Home** as the development method
5. Fill in the project details and create the project
6. After creation, find your credentials in the project **Overview** tab:
   - **Access ID/Client ID**
   - **Access Secret/Client Secret**

### Step 3: Configure the Integration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "JTMSBH MF15 Wifi Lock"
3. Enter your Tuya IoT Platform credentials:
   - **Access ID/Client ID**: From step 2 above
   - **Access Secret/Client Secret**: From step 2 above
4. Click **Submit**

The integration will automatically discover your JTMSBH devices from the existing Tuya integration.

## Entities

### Lock Entity
- **Entity Type**: `lock.your_device_name`
- **Features**: Lock/unlock control
- **States**: `locked`, `unlocked`, `unavailable`

### Battery Sensor
- **Entity Type**: `sensor.your_device_name_battery`
- **Device Class**: `battery`
- **Unit**: `%`
- **Category**: `diagnostic`

## Advanced Features

### Enhanced Local Monitoring

This integration includes optional TinyTuya monitoring for faster state updates through local network communication. **Important**: This is still polling-based, not true real-time updates.

**How Polling Works:**
- **Standard Tuya Integration**: Cloud-based polling (relies on Tuya cloud updates)
- **TinyTuya Local Mode**: 
  - Passive: Every 5 seconds (LAN) / 10 seconds (cloud fallback)
  - Fast: Every 1 second (LAN) / 2 seconds (cloud fallback) for 30 seconds after commands
- **Device Sleep Cycles**: JTMSBH locks sleep between operations to preserve battery

**Optional Dependency**: For enhanced local monitoring, install TinyTuya:
```bash
pip install tinytuya
```

**Note**: TinyTuya local mode only works when the lock is awake and connected to WiFi. The lock will periodically sleep to conserve battery, during which it cannot be polled locally.

### Battery Drain Considerations

**Polling Frequency Impact on Battery Life:**

- **Standard Tuya Integration**: Minimal battery impact as the device initiates communication
  - Lock wakes up → Sends status to cloud → Returns to sleep
  - Home Assistant receives updates from Tuya cloud
  - Battery impact: Low (recommended for most users)

- **TinyTuya Local/Cloud Polling**: Potential for increased battery drain
  - Passive polling: Every 5-10 seconds depending on connection method
  - Fast polling: Every 1-2 seconds for 30 seconds after lock/unlock commands
  - If polling keeps device awake, battery drain increases significantly
  - Benefit: Much faster state updates when device is awake
  - Battery impact: Medium to High (depending on device behavior and polling frequency)

**Recommendation**: For battery-powered smart locks, stick with cloud polling unless you need faster state updates and are willing to accept reduced battery life.

## Troubleshooting

### Common Issues

**Integration shows "Tuya not found" error**
- Ensure the official Tuya integration is installed and configured first
- Verify your JTMSBH device appears in the Tuya integration

**Lock not responding to commands**
- Check your WiFi connection and device connectivity
- Verify the device is online in the Tuya app
- Try restarting the integration or Home Assistant

**Missing battery sensor**
- Some lock models may not expose battery information
- Ensure your device firmware is up to date

**Local polling not working**
- Install TinyTuya: `pip install tinytuya`
- Verify your Tuya IoT Platform credentials are correct
- Check that your device supports local network access
- Remember: Polling only works when the lock is awake, not during sleep cycles

### Debug Logging

To enable debug logging for troubleshooting, add this to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.jtmsbh_mf15_wifi_lock: debug
```

### Getting Help

- Check the [issues page](https://github.com/jpcaldwell30/JTMSBH-MF15-Wifi-Lock/issues) for known problems
- Create a new issue with debug logs if you encounter problems
- Include your Home Assistant version and integration version

## Technical Details

### Supported Device Categories
- JTMSBH MF15 WiFi smart locks (category: `jtmsbh`)

### Dependencies
- `tuya-connector-python>=0.1.2` (for enhanced Tuya API access)
- `tinytuya` (optional, for local network polling)

### Integration Architecture
This integration extends the official Tuya integration by:
- Monitoring Tuya device registry for JTMSBH devices
- Adding specialized lock and sensor entities
- Providing enhanced local polling capabilities through TinyTuya
- Supporting both cloud and local communication methods

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- Built on top of the official Home Assistant Tuya integration
- Uses the [tuya-connector-python](https://github.com/tuya/tuya-connector-python) library
- Optional TinyTuya integration for enhanced monitoring

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/jpcaldwell30/JTMSBH-MF15-Wifi-Lock.svg?style=for-the-badge
[commits]: https://github.com/jpcaldwell30/JTMSBH-MF15-Wifi-Lock/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license]: https://github.com/jpcaldwell30/JTMSBH-MF15-Wifi-Lock/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/jpcaldwell30/JTMSBH-MF15-Wifi-Lock.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/jpcaldwell30/JTMSBH-MF15-Wifi-Lock.svg?style=for-the-badge
[releases]: https://github.com/jpcaldwell30/JTMSBH-MF15-Wifi-Lock/releases
