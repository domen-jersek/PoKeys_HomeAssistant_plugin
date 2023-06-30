from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Literal, final

from .pokeys import pokeys_instance

import voluptuous as vol

from pprint import pformat
from homeassistant.backports.enum import StrEnum
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.const import (CONF_NAME, CONF_HOST)
from homeassistant.helpers.config_validation import (  # noqa: F401
    PLATFORM_SCHEMA,
    PLATFORM_SCHEMA_BASE,
)

from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.binary_sensor import DOMAIN
from homeassistant.loader import bind_hass
from homeassistant.util import dt as dt_util
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME
from homeassistant.const import CONF_PIN
#cv = config_validation()

from .pokeys_interface import pokeys_interface
pk = pokeys_interface()
#pin = 8

_LOGGER = logging.getLogger("pokeys")

DOMAIN = "PoKeys57E"
SCAN_INTERVAL = timedelta(seconds=15)
CONF_SERIAL = "serial"

ENTITY_ID_FORMAT = DOMAIN + ".{}"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_SERIAL): cv.string,
    vol.Required(CONF_PIN): cv.string,
})

class BinarySensorDeviceClass(StrEnum):
    """Device class for binary sensors."""

    # On means low, Off means normal
    BATTERY = "battery"

    # On means charging, Off means not charging
    BATTERY_CHARGING = "battery_charging"

    # On means carbon monoxide detected, Off means no carbon monoxide (clear)
    CO = "carbon_monoxide"

    # On means cold, Off means normal
    COLD = "cold"

    # On means connected, Off means disconnected
    CONNECTIVITY = "connectivity"

    # On means open, Off means closed
    DOOR = "door"

    # On means open, Off means closed
    GARAGE_DOOR = "garage_door"

    # On means gas detected, Off means no gas (clear)
    GAS = "gas"

    # On means hot, Off means normal
    HEAT = "heat"

    # On means light detected, Off means no light
    LIGHT = "light"

    # On means open (unlocked), Off means closed (locked)
    LOCK = "lock"

    # On means wet, Off means dry
    MOISTURE = "moisture"

    # On means motion detected, Off means no motion (clear)
    MOTION = "motion"

    # On means moving, Off means not moving (stopped)
    MOVING = "moving"

    # On means occupied, Off means not occupied (clear)
    OCCUPANCY = "occupancy"

    # On means open, Off means closed
    OPENING = "opening"

    # On means plugged in, Off means unplugged
    PLUG = "plug"

    # On means power detected, Off means no power
    POWER = "power"

    # On means home, Off means away
    PRESENCE = "presence"

    # On means problem detected, Off means no problem (OK)
    PROBLEM = "problem"

    # On means running, Off means not running
    RUNNING = "running"

    # On means unsafe, Off means safe
    SAFETY = "safety"

    # On means smoke detected, Off means no smoke (clear)
    SMOKE = "smoke"

    # On means sound detected, Off means no sound (clear)
    SOUND = "sound"

    # On means tampering detected, Off means no tampering (clear)
    TAMPER = "tamper"

    # On means update available, Off means up-to-date
    UPDATE = "update"

    # On means vibration detected, Off means no vibration
    VIBRATION = "vibration"

    # On means open, Off means closed
    WINDOW = "window"


DEVICE_CLASSES_SCHEMA = vol.All(vol.Lower, vol.Coerce(BinarySensorDeviceClass))

# DEVICE_CLASS* below are deprecated as of 2021.12
# use the BinarySensorDeviceClass enum instead.
DEVICE_CLASSES = [cls.value for cls in BinarySensorDeviceClass]
DEVICE_CLASS_BATTERY = BinarySensorDeviceClass.BATTERY.value
DEVICE_CLASS_BATTERY_CHARGING = BinarySensorDeviceClass.BATTERY_CHARGING.value
DEVICE_CLASS_CO = BinarySensorDeviceClass.CO.value
DEVICE_CLASS_COLD = BinarySensorDeviceClass.COLD.value
DEVICE_CLASS_CONNECTIVITY = BinarySensorDeviceClass.CONNECTIVITY.value
DEVICE_CLASS_DOOR = BinarySensorDeviceClass.DOOR.value
DEVICE_CLASS_GARAGE_DOOR = BinarySensorDeviceClass.GARAGE_DOOR.value
DEVICE_CLASS_GAS = BinarySensorDeviceClass.GAS.value
DEVICE_CLASS_HEAT = BinarySensorDeviceClass.HEAT.value
DEVICE_CLASS_LIGHT = BinarySensorDeviceClass.LIGHT.value
DEVICE_CLASS_LOCK = BinarySensorDeviceClass.LOCK.value
DEVICE_CLASS_MOISTURE = BinarySensorDeviceClass.MOISTURE.value
DEVICE_CLASS_MOTION = BinarySensorDeviceClass.MOTION.value
DEVICE_CLASS_MOVING = BinarySensorDeviceClass.MOVING.value
DEVICE_CLASS_OCCUPANCY = BinarySensorDeviceClass.OCCUPANCY.value
DEVICE_CLASS_OPENING = BinarySensorDeviceClass.OPENING.value
DEVICE_CLASS_PLUG = BinarySensorDeviceClass.PLUG.value
DEVICE_CLASS_POWER = BinarySensorDeviceClass.POWER.value
DEVICE_CLASS_PRESENCE = BinarySensorDeviceClass.PRESENCE.value
DEVICE_CLASS_PROBLEM = BinarySensorDeviceClass.PROBLEM.value
DEVICE_CLASS_RUNNING = BinarySensorDeviceClass.RUNNING.value
DEVICE_CLASS_SAFETY = BinarySensorDeviceClass.SAFETY.value
DEVICE_CLASS_SMOKE = BinarySensorDeviceClass.SMOKE.value
DEVICE_CLASS_SOUND = BinarySensorDeviceClass.SOUND.value
DEVICE_CLASS_TAMPER = BinarySensorDeviceClass.TAMPER.value
DEVICE_CLASS_UPDATE = BinarySensorDeviceClass.UPDATE.value
DEVICE_CLASS_VIBRATION = BinarySensorDeviceClass.VIBRATION.value
DEVICE_CLASS_WINDOW = BinarySensorDeviceClass.WINDOW.value

# mypy: disallow-any-generics

#async_setup
async def async_setup_platform(hass: HomeAssistant, config: ConfigType, add_entities: AddEntitiesCallBack, discovery_info=None) -> bool:
    """Track states and offer events for binary sensors."""
    component = hass.data[DOMAIN] = EntityComponent[BinarySensorEntity](
        logging.getLogger("pokeys"), DOMAIN, hass, SCAN_INTERVAL
    )
    
    binary_sensor = {
        "name": config[CONF_NAME],
        "serial": config[CONF_SERIAL],
        "pin": config[CONF_PIN]
    }
    add_entities([
        PoKeys57E(
            hass,
            config.get(CONF_NAME),
            config.get(CONF_SERIAL),
            config.get(CONF_PIN),
        )
    ])
    _LOGGER.info(pformat(config))
    await component.async_setup(config)
    #async_add_entities([binary_sensor])
    return True

class PoKeys57E(BinarySensorEntity):
    def __init__(self, hass, name, serial, pin):
        self._serial = serial
        host = pk.device_discovery(serial)
        self._binary_sensor = pokeys_instance(host)
        self._hass = hass
        
        self._name = name
        self._pin = pin
        self._state = False
        pk.connect(host)

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state
    
    #host = PoKeys57E(config.get(CONF_HOST))
    async def async_update(self):
        # Code to read the state of your IO device
        # and set self._state accordingly
        #self._state = read_io_device_state()
        
        #pk.connect(_host) #"192.168.0.103"
        #_state = pk.read_digital_input(7)
        #self.pk.read_pin_function(pin)
        pin = self._pin
        self._state = pk.read_digital_input(int(pin)-1)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, config: ConfigType, add_entities: AddEntitiesCallBack, discovery_info=None) -> bool:
    """Set up a config entry."""

    #async_add_entities(PoKeys57E(hass, CONF_NAME, CONF_HOST))
    
    component: EntityComponent[BinarySensorEntity] = hass.data[DOMAIN]
    return await component.async_setup_entry(entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    #async_add_entities(PoKeys57E(hass, CONF_NAME, CONF_HOST))

    component: EntityComponent[BinarySensorEntity] = hass.data[DOMAIN]
    return await component.async_unload_entry(entry)


@dataclass
class BinarySensorEntityDescription(EntityDescription):
    """A class that describes binary sensor entities."""

    device_class: BinarySensorDeviceClass | None = None


class BinarySensorEntity(Entity):
    """Represent a binary sensor."""

    entity_description: BinarySensorEntityDescription
    _attr_device_class: BinarySensorDeviceClass | None
    _attr_is_on: bool | None = None
    _attr_state: None = None

    def __init__(self, hass, name, serial, pin):
        self._serial = serial
        host = pk.device_discovery(serial)
        self._binary_sensor = pokeys_instance(host)
        self._hass = hass
        
        self._name = name
        self._pin = pin
        self._state = False
        pk.connect(host)

    @property
    def name(self):
        return self._name

    #@property
    #def is_on(self):
    #    return self._state

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        """Return the class of this entity."""
        if hasattr(self, "_attr_device_class"):
            return self._attr_device_class
        if hasattr(self, "entity_description"):
            return self.entity_description.device_class
        return None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        
        #pk.connect("192.168.0.103")
        pin = self._pin
        if pk.read_digital_input(int(pin)-1) == "on":
            return self._attr_is_on
        return self._state

    @final
    @property
    def state(self) -> Literal["on", "off"] | None:
        """Return the state of the binary sensor."""
        if (is_on := self.is_on) is None:
            return None
        return STATE_ON if is_on else STATE_OFF