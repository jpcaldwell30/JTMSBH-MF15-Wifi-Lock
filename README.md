# HASS-Tuya-Wifi-Lock

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

This integration is an attempt to bring Tuya wifi lock compatibility to Home Assistant. It adds a lock entity to the Tuya integration. Currently, it only has support for my lock (type "jtmsbh" on the Tuya website) but I will explain how to add support for your lock below. This integration overrides the core Tuya integration. It is based on the core home assistant Tuya integeation as of commit [b323295](https://github.com/home-assistant/core/tree/b323295aa15ff6ac81e46b213a2f22440f0460de), so if you use this in the future, it might be worth cloning the repository and updating the core Tuya integration files (minus the changes you will make below documented in usage).

## Installation instructions

First make sure you have setup the core Tuya Home Assistant integration and have your supported devices and your lock are already added to Home Assistant. Instructions for how to do this can be found here: [Tuya](https://www.home-assistant.io/integrations/tuya/)

- Install using [HACS](https://hacs.xyz) (Or copy the contents of `custom_components/tuya/` to `<your config dir>/custom_components/tuya/`.)

- Restart Home Assistant

- Follow the instrctions below to add support for your lock. After adding the necesarry code, you're lock should automatically show up in Home Asssistant

## Adding suport for your lock
First, follow the instructions found here to locate the neceary DPCodes that reflect the different states of your lock. https://dubble.so/guides/getting-tuya-lock-dpcodes-r8aouvwmkjb0q0equh8e

Once you have your lock's DPCodes, open the const.py file from this repo. Add two easily rememberable DPCode entries in the form NAME="<DPcode>". One for the lock state DPCode and one for the lock battery DPCode. for example, I set mine as:

M15_WIFI_01_LOCK_STATE = "lock_motor_state"

M15_WIFI_01_BATTERY_PERCENTAGE = "residual_electricity"

Also make sure to add the lock platform anywhere within the Platforms dict: <Platform.LOCK,>

Next, open lock.py file from this repo. Uncomment out the example entry (starting at line 28) and fill in with the info for your locks catagory, and the DPcode you defined for the lock status previosly.
If your lock uses a non standard DPCode for determining it's status (standard is true: unlocked door, false: locked door), then you can update your expected value for the locks locked/unlocked states on line 24 and 25

Finally, open the sensor.py. Uncomment out the example entry (starting at line 85) and fill in with the info for your locks catagory, and the DPcode you defined for the lock BATTERY status previosly.

Save these changes and reboot home assitant. Your lock should show up automatically. 
