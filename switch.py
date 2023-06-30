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
from homeassistant.const import (CONF_NAME, CONF_PIN) #, CONF_SERIAL
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

from .pokeys_interface import pokeys_interface

_LOGGER = logging.getLogger("pokeys")

pk = pokeys_interface()

DOMAIN = "PoKeys57E"
#pin = 12
CONF_SERIAL = "serial"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_SERIAL): cv.string,
    vol.Required(CONF_PIN): cv.string,
})
#vol.Required(CONF_PIN): cv.string,
#CONF_PIN = "pin"
#pin = config.get(CONF_PIN)

def setup_platform(hass: HomeAssistant, config: ConfigType, add_entities: AddEntitiesCallBack, discovery_info=None):
    #pin = config.get(CONF_PIN)

    switch = {
        "name": config[CONF_NAME],
        "serial": config[CONF_SERIAL],
        "pin": config[CONF_PIN]        
    }#"pin": config[CONF_PIN]
    
    add_entities([
        PoKeys57E(
            hass,
            config.get(CONF_NAME),
            config.get(CONF_SERIAL),
            config.get(CONF_PIN),
        )
    ])
    #config.get(CONF_PIN),
    _LOGGER.info(pformat(config))
    

class PoKeys57E(SwitchEntity):

    def __init__(self, hass, name, serial, pin): #, pin
        #_LOGGER.info(pformat(config))
        self._serial = serial
        host = pk.device_discovery(serial)
        self._switch = pokeys_instance(host)

        self._hass = hass
        self._name = name  #config[CONF_NAME]
        self._pin = pin
        self._state = None
        
        pk.connect(host)

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state
    
    def turn_on(self, **kwargs): 
        #config_entry = self.hass.config_entries.async_get_entry(self.config_entry_id)
        #config = self.hass.config_entries
        #pin = self.hass.config_entries(CONF_PIN)
        #host = pk.device_discovery(serial)
        #pk.connect(host)
        pin = self._pin
        pk.set_pin_function(int(pin)-1, 4)
        # Implement switch on logic here
        self._state = True
        self.schedule_update_ha_state()


    def turn_off(self, **kwargs):
        """Turn the switch off."""
        # Implement switch off logic here
        #config = self.hass.config_entries
        #pin = self.hass.config_entries(CONF_PIN)
        #host = pk.device_discovery(serial)
        #pk.connect(host)
        pin = self._pin
        pk.set_pin_function(int(pin)-1, 2)
        self._state = False
        self.schedule_update_ha_state()
