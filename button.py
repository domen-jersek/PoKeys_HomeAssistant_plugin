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
from homeassistant.components.button import (PLATFORM_SCHEMA, PLATFORM_SCHEMA_BASE, ButtonEntity)
from homeassistant.const import (CONF_NAME, CONF_HOST)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import bind_hass

from homeassistant.util import dt as dt_util
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.const import (CONF_NAME, CONF_HOST)
import time

from .pokeys_interface import pokeys_interface

_LOGGER = logging.getLogger("pokeys")
pk = pokeys_interface()
DOMAIN = "PoKeys57E"
pin = 13

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
})

async def async_setup_platform(hass: HomeAssistant, config: ConfigType, add_entities: AddEntitiesCallBack, discovery_info=None): #hass, config, async_add_entities, discovery_info=None
    """Set up the custom button platform."""

    button = {
        "name": config[CONF_NAME],
        "host": config[CONF_HOST]
    }
    add_entities([
        PoKeys57E(
            hass,
            config.get(CONF_NAME),
            config.get(CONF_HOST),
        )
    ])

    _LOGGER.info(pformat(config))
    
class PoKeys57E(ButtonEntity):
    """Define the custom button entity."""
    
    def __init__(self, hass, name, host):
        """Initialize the button entity."""
        self._button = pokeys_instance(host)

        self._hass = hass
        self._name = name
        self._host = host
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
    
    async def async_press(self) -> None:
        self._state = "pressed"
        _LOGGER.info("Custom button pressed.")
        pk.set_pin_function(pin-1, 4)
        time.sleep(5)
        self._state = "released"
        _LOGGER.info("Custom button released.")
        pk.set_pin_function(pin-1, 2)
    
    async def async_turn_off(self): #, **kwargs
        """Perform any actions when the button is turned off."""
        self._state = "released"
        _LOGGER.info("Custom button released.")
        pk.set_pin_function(pin-1, 2)
