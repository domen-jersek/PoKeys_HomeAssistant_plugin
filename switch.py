from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
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
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import bind_hass
from custom_components import pokeys
import threading

from homeassistant.components.switch import DOMAIN

SCAN_INTERVAL = timedelta(seconds=1)

from .pokeys_interface import pokeys_interface

_LOGGER = logging.getLogger("pokeys")

ENTITY_ID_FORMAT = DOMAIN + ".{}"

pk = pokeys_interface()

DOMAIN = "pokeys"
CONF_SERIAL = "serial"
CONF_DEVICE = "device"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_SERIAL): cv.string,
    vol.Optional(CONF_DEVICE): cv.string,
    vol.Required(CONF_PIN): cv.string,
})

class SwitchDeviceClass(StrEnum):
    """Device class for switches."""

    OUTLET = "outlet"
    SWITCH = "switch"

DEVICE_CLASSES_SCHEMA = vol.All(vol.Lower, vol.Coerce(SwitchDeviceClass))
DEVICE_CLASSES = [cls.value for cls in SwitchDeviceClass]
DEVICE_CLASS_OUTLET = SwitchDeviceClass.OUTLET.value
DEVICE_CLASS_SWITCH = SwitchDeviceClass.SWITCH.value

mutex = threading.Lock()

async def async_setup_platform(hass: HomeAssistant, config: ConfigType, async_add_entities: AddEntitiesCallBack, discovery_info=None):
    component = hass.data[DOMAIN] = EntityComponent[SwitchEntity](
        _LOGGER, DOMAIN, hass, SCAN_INTERVAL
    )


    switches = hass.data.get("switches", None)
    platform_run = True

    try:
        switch = {
            "name": config[CONF_NAME],
            "serial": config[CONF_SERIAL],
            "pin": config[CONF_PIN]
        }
        async_add_entities([
            PoKeys57E(
                hass,
                config.get(CONF_NAME),
                config.get(CONF_SERIAL),
                config.get(CONF_PIN)
            )
        ])
        platform_run = False
    except:
        pass
    
    try:
        if platform_run:
            for switch in switches:
                switch = {
                    "name": switch[0],
                    "serial": switch[1],
                    "pin": switch[2],
                }
                async_add_entities([
                    PoKeys57E(
                        hass,
                        switch["name"],
                        switch["serial"],
                        switch["pin"]
                    )
                ])
    except:
        pass
    
    await component.async_setup(config)

    component.async_register_entity_service(SERVICE_TURN_OFF, {}, "async_turn_off")
    component.async_register_entity_service(SERVICE_TURN_ON, {}, "async_turn_on")
    component.async_register_entity_service(SERVICE_TOGGLE, {}, "async_toggle")

    _LOGGER.info(pformat(config))

    return True
    

class PoKeys57E(SwitchEntity):

    def __init__(self, hass, name, serial, pin): 
        self._serial = serial
        self._host = pk.device_discovery(self._serial)
        self._switch = pokeys_instance(self._host)

        self._hass = hass
        self._name = name  
        self._pin = pin
        self._state = None
        self._inputs_updated = self._hass.data.get("inputs_updated", None)
        self._inputs = self._hass.data.get("inputs", None)
        
        self._hosts = self._hass.data.get("hosts", None)
        pk.connect(self._host)
        pk.set_pin_function(int(pin)-1, 4)

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state
    
    def turn_on(self): 
        pin = self._pin
        pk.connect(self._host)
        pk.set_output(int(pin)-1, 1)
        
        self._inputs_updated.wait(timeout=None)
        while self._hass.data.get("host_cycle", None) != self._host:
            pass
        
        if self._inputs[self._hosts.index(self._host)][int(pin)-1]:
            self._state = True
        
        self.schedule_update_ha_state()


    def turn_off(self):#, **kwargs
        pin = self._pin
        pk.connect(self._host)
        pk.set_output(int(pin)-1, 0)
        
        self._inputs_updated.wait(timeout=None)
        while self._hass.data.get("host_cycle", None) != self._host:
            pass
        
        if self._inputs[self._hosts.index(self._host)][int(pin)-1] == False:
            self._state = False
        self.schedule_update_ha_state()

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    component: EntityComponent[SwitchEntity] = hass.data[DOMAIN]
    return await component.async_setup_entry(entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    component: EntityComponent[SwitchEntity] = hass.data[DOMAIN]
    return await component.async_unload_entry(entry)

@dataclass
class SwitchEntityDescription(ToggleEntityDescription):
    """A class that describes switch entities."""

    device_class: SwitchDeviceClass | None = None


class SwitchEntity(ToggleEntity):
    """Base class for switch entities."""

    entity_description: SwitchEntityDescription
    _attr_device_class: SwitchDeviceClass | None

    def __init__(self, hass, name, serial, pin): 
        self._serial = serial
        self._host = pk.device_discovery(serial)
        self._switch = pokeys_instance(self._host)

        self._hass = hass
        self._name = name  
        self._pin = pin
        self._state = None
        self._inputs_updated = self._hass.data.get("inputs_updated", None)
        self._inputs = self._hass.data.get("inputs", None)
        
        self._hosts = self._hass.data.get("hosts", None)
        pk.connect(self._host)
        pk.set_pin_function(int(pin)-1, 4)

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state
    
    def turn_on(self): 
        pin = self._pin
        pk.connect(self._host)
        pk.set_output(int(pin)-1, 1)
        
        self._inputs_updated.wait(timeout=None)
        while self._hass.data.get("host_cycle", None) != self._host:
            pass
        
        if self._inputs[self._hosts.index(self._host)][int(pin)-1]:
            self._state = True
        self.schedule_update_ha_state()


    def turn_off(self):
        pin = self._pin
        pk.connect(self._host)
        pk.set_output(int(pin)-1, 0)
        
        self._inputs_updated.wait(timeout=None)
        while self._hass.data.get("host_cycle", None) != self._host:
            pass
        
        if self._inputs[self._hosts.index(self._host)][int(pin)-1] == False:
            self._state = False
        self.schedule_update_ha_state()

    @property
    def device_class(self) -> SwitchDeviceClass | None:
        """Return the class of this entity."""
        if hasattr(self, "_attr_device_class"):
            return self._attr_device_class
        if hasattr(self, "entity_description"):
            return self.entity_description.device_class
        return None
