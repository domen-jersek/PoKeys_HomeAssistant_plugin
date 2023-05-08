from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from .pokeys import pokeys_instance

from pprint import pformat
from homeassistant.backports.enum import StrEnum
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.switch import (PLATFORM_SCHEMA, PLATFORM_SCHEMA_BASE, SwitchEntity)  #, SwitchDevice
from homeassistant.const import (CONF_NAME, CONF_HOST)
from homeassistant.const import (
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import ToggleEntity, ToggleEntityDescription
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import bind_hass

#from .const import DOMAIN

from .pokeys_interface import pokeys_interface

_LOGGER = logging.getLogger("pokeys")

pk = pokeys_interface()

DOMAIN = "PoKeys57E"
#pin = data.get("pin")
pin = 12

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
})

def setup_platform(hass: HomeAssistant, config: ConfigType, add_entities: AddEntitiesCallBack, discovery_info=None):

    switch = {
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
    #add_entities([PoKeys57E(switch)])
    """switch = {
        "name": config.get(CONF_NAME),
        "host": config.get(CONF_HOST)
    }

    add_entities([
        PoKeys57E(hass, switch["name"], switch["host"], config)
    ])"""
    _LOGGER.info(pformat(config))
    

class PoKeys57E(SwitchEntity): #SwitchDevice

    def __init__(self, hass, name, host):
        
        #_LOGGER.info(pformat(config))
        self._switch = pokeys_instance(host)

        self._hass = hass
        self._name = name  #config[CONF_NAME]
        self._host = host  #config[CONF_HOST]
        self._state = None
        pk.connect(host)

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        #pk.set_pin_function(11, 4)
        """if not _send: #pk.connect(switch(["host"]))
            _LOGGER.error("Not available")
        else:
            _LOGGER.error("avalible")"""
        return self._state

    def turn_on(self, **kwargs):
        
        pk.set_pin_function(pin-1, 4)
        # Implement switch on logic here
        self._state = True
        self.schedule_update_ha_state()
        #pk.set_output(12, True)


    def turn_off(self, **kwargs):
        """Turn the switch off."""
        # Implement switch off logic here
        pk.set_pin_function(pin-1, 2)
        self._state = False
        self.schedule_update_ha_state()
        #pk.set_output(12, False)
