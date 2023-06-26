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
from homeassistant.const import (CONF_NAME, CONF_HOST, CONF_PIN)
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
#from .const import DOMAIN #, SERVICE_PRESS
import time

from .pokeys_interface import pokeys_interface

_LOGGER = logging.getLogger("pokeys")
pk = pokeys_interface()
DOMAIN = "PoKeys57E"
#pin = 13

# Define a platform schema that includes the required configuration options
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_PIN): cv.string,
})

async def async_setup_platform(hass: HomeAssistant, config: ConfigType, add_entities: AddEntitiesCallBack, discovery_info=None): #hass, config, async_add_entities, discovery_info=None
    """Set up the custom button platform."""
    #name = config.get(CONF_NAME)
    #host = config.get(CONF_HOST)
    button = {
        "name": config[CONF_NAME],
        "host": config[CONF_HOST],
        "pin": config[CONF_PIN]
    }
    add_entities([
        PoKeys57E(
            hass,
            config.get(CONF_NAME),
            config.get(CONF_HOST),
            config.get(CONF_PIN)
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
    
    def __init__(self, hass, name, host, pin):
        """Initialize the button entity."""
        self._button = pokeys_instance(host)

        self._hass = hass
        self._name = name
        self._host = host
        self._pin = pin
        self._state = "released"
        pk.connect(host)
    
    @property
    def name(self):
        """Return the name of the button entity."""
        return self._name
    
    @property
    def icon(self):
        """Return the icon for the button entity."""
        return "mdi:gesture-double-tap"
    
    @property
    def state(self):
        """Return the current state of the button entity."""
        return self._state
    
    async def async_added_to_hass(self):
        """Perform any actions when the button entity is added to Home Assistant."""
        _LOGGER.info("Custom button entity added to Home Assistant.")
    
    async def async_will_remove_from_hass(self):
        """Perform any actions when the button entity is removed from Home Assistant."""
        _LOGGER.info("Custom button entity removed from Home Assistant.")
    
    def press(self) -> None:
        self._state = "pressed"
        _LOGGER.info("Custom button pressed.")
        pin = self._pin
        pk.set_pin_function(int(pin)-1, 4)
        time.sleep(5)
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