"""Constants for the Tuya integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
import logging

from tuya_iot import TuyaCloudOpenAPIEndpoint

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    Platform,
)

DOMAIN = "jtmsbh_mf15_wifi_lock"
LOGGER = logging.getLogger(__package__)

CONF_AUTH_TYPE = "auth_type"
CONF_PROJECT_TYPE = "tuya_project_type"
CONF_ENDPOINT = "endpoint"
CONF_ACCESS_ID = "access_id"
CONF_ACCESS_SECRET = "access_secret"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_COUNTRY_CODE = "country_code"
CONF_APP_TYPE = "tuya_app_type"

TUYA_DISCOVERY_NEW = "tuya_discovery_new"
TUYA_HA_SIGNAL_UPDATE_ENTITY = "tuya_entry_update"

TUYA_RESPONSE_CODE = "code"
TUYA_RESPONSE_RESULT = "result"
TUYA_RESPONSE_MSG = "msg"
TUYA_RESPONSE_SUCCESS = "success"
TUYA_RESPONSE_PLATFORM_URL = "platform_url"

TUYA_SMART_APP = "tuyaSmart"
SMARTLIFE_APP = "smartlife"

POWER="POWER"

PLATFORMS = [
    Platform.LOCK,
    Platform.SENSOR,
]

class DPType(StrEnum):
    """Data point types."""

    BOOLEAN = "Boolean"
    ENUM = "Enum"
    INTEGER = "Integer"
    JSON = "Json"
    RAW = "Raw"
    STRING = "String"


class DPCode(StrEnum):
    """Data Point Codes used by Tuya.

    https://developer.tuya.com/en/docs/iot/standarddescription?id=K9i5ql6waswzq
    """
    M15_WIFI_01_LOCK_STATE = "lock_motor_state"
    M15_WIFI_01_BATTERY_PERCENTAGE = "residual_electricity"



@dataclass
class UnitOfMeasurement:
    """Describes a unit of measurement."""

    unit: str
    device_classes: set[str]

    aliases: set[str] = field(default_factory=set)
    conversion_unit: str | None = None
    conversion_fn: Callable[[float], float] | None = None


# A tuple of available units of measurements we can work with.
# Tuya's devices aren't consistent in UOM use, thus this provides
# a list of aliases for units and possible conversions we can do
# to make them compatible with our model.
UNITS = (
    UnitOfMeasurement(
        unit="",
        aliases={" "},
        device_classes={
            SensorDeviceClass.AQI,
            SensorDeviceClass.DATE,
            SensorDeviceClass.MONETARY,
            SensorDeviceClass.TIMESTAMP,
        },
    ),
    UnitOfMeasurement(
        unit=PERCENTAGE,
        aliases={"pct", "percent", "% RH"},
        device_classes={
            SensorDeviceClass.BATTERY,
        },
    ),
)


DEVICE_CLASS_UNITS: dict[str, dict[str, UnitOfMeasurement]] = {}
for uom in UNITS:
    for device_class in uom.device_classes:
        DEVICE_CLASS_UNITS.setdefault(device_class, {})[uom.unit] = uom
        for unit_alias in uom.aliases:
            DEVICE_CLASS_UNITS[device_class][unit_alias] = uom


@dataclass
class Country:
    """Describe a supported country."""

    name: str
    country_code: str
    endpoint: str = TuyaCloudOpenAPIEndpoint.AMERICA


# https://developer.tuya.com/en/docs/iot/oem-app-data-center-distributed?id=Kafi0ku9l07qb
TUYA_COUNTRIES = [
    Country("Afghanistan", "93", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Albania", "355", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Algeria", "213", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("American Samoa", "1-684", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Andorra", "376", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Angola", "244", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Anguilla", "1-264", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Antarctica", "672", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Antigua and Barbuda", "1-268", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Argentina", "54", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Armenia", "374", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Aruba", "297", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Australia", "61", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Austria", "43", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Azerbaijan", "994", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Bahamas", "1-242", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Bahrain", "973", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Bangladesh", "880", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Barbados", "1-246", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Belarus", "375", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Belgium", "32", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Belize", "501", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Benin", "229", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Bermuda", "1-441", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Bhutan", "975", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Bolivia", "591", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Bosnia and Herzegovina", "387", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Botswana", "267", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Brazil", "55", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("British Indian Ocean Territory", "246", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("British Virgin Islands", "1-284", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Brunei", "673", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Bulgaria", "359", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Burkina Faso", "226", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Burundi", "257", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Cambodia", "855", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Cameroon", "237", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Canada", "1", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Capo Verde", "238", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Cayman Islands", "1-345", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Central African Republic", "236", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Chad", "235", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Chile", "56", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("China", "86", TuyaCloudOpenAPIEndpoint.CHINA),
    Country("Christmas Island", "61"),
    Country("Cocos Islands", "61"),
    Country("Colombia", "57", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Comoros", "269", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Cook Islands", "682", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Costa Rica", "506", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Croatia", "385", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Cuba", "53"),
    Country("Curacao", "599", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Cyprus", "357", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Czech Republic", "420", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Democratic Republic of the Congo", "243", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Denmark", "45", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Djibouti", "253", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Dominica", "1-767", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Dominican Republic", "1-809", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("East Timor", "670", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Ecuador", "593", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Egypt", "20", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("El Salvador", "503", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Equatorial Guinea", "240", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Eritrea", "291", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Estonia", "372", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Ethiopia", "251", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Falkland Islands", "500", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Faroe Islands", "298", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Fiji", "679", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Finland", "358", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("France", "33", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("French Polynesia", "689", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Gabon", "241", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Gambia", "220", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Georgia", "995", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Germany", "49", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Ghana", "233", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Gibraltar", "350", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Greece", "30", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Greenland", "299", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Grenada", "1-473", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Guam", "1-671", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Guatemala", "502", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Guernsey", "44-1481"),
    Country("Guinea", "224"),
    Country("Guinea-Bissau", "245", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Guyana", "592", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Haiti", "509", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Honduras", "504", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Hong Kong", "852", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Hungary", "36", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Iceland", "354", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("India", "91", TuyaCloudOpenAPIEndpoint.INDIA),
    Country("Indonesia", "62", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Iran", "98"),
    Country("Iraq", "964", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Ireland", "353", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Isle of Man", "44-1624"),
    Country("Israel", "972", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Italy", "39", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Ivory Coast", "225", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Jamaica", "1-876", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Japan", "81", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Jersey", "44-1534"),
    Country("Jordan", "962", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Kazakhstan", "7", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Kenya", "254", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Kiribati", "686", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Kosovo", "383"),
    Country("Kuwait", "965", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Kyrgyzstan", "996", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Laos", "856", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Latvia", "371", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Lebanon", "961", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Lesotho", "266", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Liberia", "231", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Libya", "218", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Liechtenstein", "423", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Lithuania", "370", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Luxembourg", "352", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Macao", "853", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Macedonia", "389", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Madagascar", "261", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Malawi", "265", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Malaysia", "60", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Maldives", "960", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Mali", "223", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Malta", "356", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Marshall Islands", "692", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Mauritania", "222", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Mauritius", "230", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Mayotte", "262", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Mexico", "52", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Micronesia", "691", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Moldova", "373", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Monaco", "377", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Mongolia", "976", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Montenegro", "382", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Montserrat", "1-664", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Morocco", "212", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Mozambique", "258", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Myanmar", "95", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Namibia", "264", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Nauru", "674", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Nepal", "977", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Netherlands", "31", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Netherlands Antilles", "599"),
    Country("New Caledonia", "687", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("New Zealand", "64", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Nicaragua", "505", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Niger", "227", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Nigeria", "234", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Niue", "683", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("North Korea", "850"),
    Country("Northern Mariana Islands", "1-670", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Norway", "47", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Oman", "968", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Pakistan", "92", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Palau", "680", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Palestine", "970", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Panama", "507", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Papua New Guinea", "675", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Paraguay", "595", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Peru", "51", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Philippines", "63", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Pitcairn", "64"),
    Country("Poland", "48", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Portugal", "351", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Puerto Rico", "1-787, 1-939", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Qatar", "974", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Republic of the Congo", "242", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Reunion", "262", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Romania", "40", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Russia", "7", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Rwanda", "250", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Saint Barthelemy", "590", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Saint Helena", "290"),
    Country("Saint Kitts and Nevis", "1-869", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Saint Lucia", "1-758", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Saint Martin", "590", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Saint Pierre and Miquelon", "508", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country(
        "Saint Vincent and the Grenadines", "1-784", TuyaCloudOpenAPIEndpoint.EUROPE
    ),
    Country("Samoa", "685", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("San Marino", "378", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Sao Tome and Principe", "239", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Saudi Arabia", "966", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Senegal", "221", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Serbia", "381", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Seychelles", "248", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Sierra Leone", "232", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Singapore", "65", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Sint Maarten", "1-721", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Slovakia", "421", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Slovenia", "386", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Solomon Islands", "677", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Somalia", "252", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("South Africa", "27", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("South Korea", "82", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("South Sudan", "211"),
    Country("Spain", "34", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Sri Lanka", "94", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Sudan", "249"),
    Country("Suriname", "597", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Svalbard and Jan Mayen", "4779", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Swaziland", "268", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Sweden", "46", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Switzerland", "41", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Syria", "963"),
    Country("Taiwan", "886", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Tajikistan", "992", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Tanzania", "255", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Thailand", "66", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Togo", "228", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Tokelau", "690", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Tonga", "676", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Trinidad and Tobago", "1-868", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Tunisia", "216", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Turkey", "90", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Turkmenistan", "993", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Turks and Caicos Islands", "1-649", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Tuvalu", "688", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("U.S. Virgin Islands", "1-340", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Uganda", "256", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Ukraine", "380", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("United Arab Emirates", "971", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("United Kingdom", "44", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("United States", "1", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Uruguay", "598", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Uzbekistan", "998", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Vanuatu", "678", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Vatican", "379", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Venezuela", "58", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Vietnam", "84", TuyaCloudOpenAPIEndpoint.AMERICA),
    Country("Wallis and Futuna", "681", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Western Sahara", "212", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Yemen", "967", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Zambia", "260", TuyaCloudOpenAPIEndpoint.EUROPE),
    Country("Zimbabwe", "263", TuyaCloudOpenAPIEndpoint.EUROPE),
]
