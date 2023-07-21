from __future__ import annotations
import logging

from dataclasses import dataclass
from datetime import timedelta
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .pokeys import pokeys_instance

from homeassistant.core import HomeAssistant

from pprint import pformat
from homeassistant.backports.enum import StrEnum
from homeassistant.config_entries import ConfigEntry
#from homeassistant.const import CONF_NAME, CONF_HOST
#from homeassistant.components.button import ButtonEntity, PLATFORM_SCHEMA
from homeassistant.components.button import (PLATFORM_SCHEMA, PLATFORM_SCHEMA_BASE, ButtonEntity) #, ButtonEntity
from homeassistant.const import (CONF_NAME, CONF_PIN) #, CONF_SERIAL
#from homeassistant.const import (
#    SERVICE_TURN_OFF,
#    SERVICE_TURN_ON,
#    STATE_ON,
#)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import bind_hass

from homeassistant.util import dt as dt_util
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity_platform import EntityPlatform
from typing import TypedDict
from homeassistant.helpers.entity import generate_entity_id
#from .const import DOMAIN #, SERVICE_PRESS
import time
#from . import __init__ as init
#from .__init__ import async_setup
#from.__init__ import PLATFORM_SCHEMA as ps


from .pokeys_interface import pokeys_interface
#from . import pokeys

#CONF_NAME = "name"
CONF_SERIAL = "serial"
CONF_DELAY = "delay"
#CONF_PIN = "pin"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_SERIAL): cv.string,
        vol.Optional(CONF_PIN): cv.string,
        vol.Optional(CONF_DELAY): cv.string,
})

_LOGGER = logging.getLogger("pokeys")
pk = pokeys_interface()
DOMAIN = "PoKeys57E"
#pin = 13

#buttons = init.async_setup(HomeAssistant, ConfigType).buttons
#logging.error(buttons)


# Define a platform schema that includes the required configuration options
#plat = await async_setup(HomeAssistant, ConfigType)
#PLATFORM_SCHEMA = ps

#, name_button, serial, pin_button
async def async_setup_platform(hass: HomeAssistant, config: ConfigType, async_add_entities: AddEntitiesCallBack, discovery_info=None): #hass, config, async_add_entities, discovery_info=None
    """Set up the custom button platform."""
    #name = config.get(CONF_NAME)
    #host = config.get(CONF_HOST)
    button = {
        "name": config[CONF_NAME],
        "serial": config[CONF_SERIAL],
        "pin": config[CONF_PIN],
        "delay": config[CONF_DELAY]
    }
    logging.error(button)
    async_add_entities([
        PoKeys57E(
            hass,
            config.get(CONF_NAME),
            config.get(CONF_SERIAL),
            config.get(CONF_PIN),
            config.get(CONF_DELAY)
            #button["name"],
            #button["serial"],
            #button["pin"]
        )
    ])

    # Create the custom button entity
    #button = PoKeys57E(hass, name, host)
    _LOGGER.info(pformat(config))
    # Add the entity to Home Assistant
    #async_add_entities([button])
    #add_entities([PoKeys57E(button)])


class PoKeys57E(ButtonEntity):
    """Define the custom button entity."""
    
    def __init__(self, hass, name, serial, pin, delay):
        """Initialize the button entity."""
        #_attr_has_entity_name = True
        #pk = pokeys_interface()
        self._serial = serial
        host = pk.device_discovery(serial)
        self._button = pokeys_instance(host)

        self._hass = hass
        self._name = name
        self._pin = pin
        self._delay = delay
        #self._platform = platform
        self._state = "released"
        #self.entity_id = generate_entity_id("button.{}", self._name, hass)
        
        pk.connect(host)
        if pk.connect(host):
            logging.error("connected")
        logging.error(self._name)
        logging.error(self._serial)
        #logging.error(self._state)
        logging.error(self._pin)
        logging.error(self._button)

    #@property
    #def platform(self):
    #    return self._platform

    @property
    def name(self):
        """Return the name of the button entity."""
        return self._name
        
    @property
    def icon(self):
        """Return the icon for the button entity."""
        return "mdi:gesture-double-tap"
    
    @property
    def state(self) -> str | None:
        """Return the current state of the button entity."""
        return self._state
        
    
    async def async_added_to_hass(self):
        """Perform any actions when the button entity is added to Home Assistant."""
        _LOGGER.info("Custom button entity added to Home Assistant.")
        #logging.error(PLATFORM_SCHEMA)
        logging.error("added to hass")
    
    async def async_will_remove_from_hass(self):
        """Perform any actions when the button entity is removed from Home Assistant."""
        _LOGGER.info("Custom button entity removed from Home Assistant.")
        logging.error("removed from hass")
    

    def press(self) -> None:
        self._state = "pressed"
        #logging.error("button pressed")
        _LOGGER.info("Custom button pressed.")
        pin = self._pin
        delay =self._delay
        pk.set_pin_function(int(pin)-1, 4)
        time.sleep(int(delay))
        self._state = "released"
        _LOGGER.info("Custom button released.")
        pk.set_pin_function(int(pin)-1, 2)
    
    def turn_off(self): #, **kwargs
        """Perform any actions when the button is turned off."""
        self._state = "released"
        _LOGGER.info("Custom button released.")
        pk.set_pin_function(pin-1, 2)

        
'''    async def async_turn_on(self, **kwargs):
        """Perform any actions when the button is turned on."""
        self._state = "pressed"
        _LOGGER.info("Custom button pressed.")
        pk.set_pin_function(pin, 4)'''