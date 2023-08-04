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
from homeassistant.const import (CONF_NAME, CONF_PIN) 
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import bind_hass
from homeassistant.helpers.entity import Entity
from homeassistant.util import dt as dt_util
from homeassistant.helpers.entity import EntityDescription
from homeassistant.components.button import DOMAIN
from homeassistant.core import callback


from homeassistant.helpers.entity_platform import EntityPlatform
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import EntityDescription
from typing import TypedDict, Literal, final
import time
from custom_components import pokeys
import threading


from .pokeys_interface import pokeys_interface

CONF_SERIAL = "serial"
CONF_DELAY = "delay"
DOMAIN = "pokeys"

SCAN_INTERVAL = timedelta(seconds=1)
SERVICE_PRESS = "press"

ENTITY_ID_FORMAT = DOMAIN + ".{}"

_LOGGER = logging.getLogger("pokeys")


class ButtonDeviceClass(StrEnum):

    IDENTIFY = "identify"
    RESTART = "restart"
    UPDATE = "update"

DEVICE_CLASSES_SCHEMA = vol.All(vol.Lower, vol.Coerce(ButtonDeviceClass))

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_SERIAL): cv.string,
        vol.Optional(CONF_PIN): cv.string,
        vol.Optional(CONF_DELAY): cv.string,
})

pk = pokeys_interface()

async def async_setup_platform(hass: HomeAssistant, config: ConfigType, async_add_entities: AddEntitiesCallBack, discovery_info=None): #hass, config, async_add_entities, discovery_info=None
    """Set up the custom button platform."""
    component = hass.data[DOMAIN] = EntityComponent[ButtonEntity](
        logging.getLogger("pokeys"), DOMAIN, hass, SCAN_INTERVAL
    )

    buttons = hass.data.get("buttons", None)
    
    platform_run = True
    
    try:
        button = {
            "name": config[CONF_NAME],
            "serial": config[CONF_SERIAL],
            "pin": config[CONF_PIN],
            "delay": config[CONF_DELAY]
        }
        async_add_entities([
            PoKeys57E(
                hass,
                config.get(CONF_NAME),
                config.get(CONF_SERIAL),
                config.get(CONF_PIN),
                config.get(CONF_DELAY)
            )
        ])
        platform_run = False
    except:
        pass
    try:
        if platform_run:
            for button in buttons:
                button = {
                    "name": button[0],
                    "serial": button[1],
                    "pin": button[2],
                    "delay": button[3],
                }
                async_add_entities([
                    PoKeys57E(
                        hass,
                        button["name"],
                        button["serial"],
                        button["pin"],
                        button["delay"]
                    )
                ])
    except:
        pass    
        

    await component.async_setup(config)

    component.async_register_entity_service(
        SERVICE_PRESS,
        {},
        "_async_press_action",
    )
    
    
    # Create the custom button entity
    #button = PoKeys57E(hass, name, host)
    _LOGGER.info(pformat(config))
    # Add the entity to Home Assistant
    #async_add_entities([button])
    #add_entities([PoKeys57E(button)])
    return True


class PoKeys57E(ButtonEntity):
    def __init__(self, hass, name, serial, pin, delay):
        """Initialize the button entity."""
        self._serial = serial
        self._host = pk.device_discovery(self._serial)
        self._button = pokeys_instance(self._host)

        self._hass = hass
        self._name = name
        self._pin = pin
        self._delay = delay
        
        self._state = "released"
        self._inputs_updated = self._hass.data.get("inputs_updated", None)
        self._inputs = self._hass.data.get("inputs", None)
        self._hosts = self._hass.data.get("hosts", None)
        self._host_cycle = self._hass.data.get("host_cycle", None)
        
        #self._devices = self._hass.data.get("devices", None)
        
        #self._host_holder = self._hass.data["host_holder"]
        

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
        
        pk.connect(self._host)
        pk.set_pin_function(int(self._pin)-1, 4)
        pk.set_output(int(self._pin)-1, 0)
        #logging.error(self._name)
        #logging.error(self._hosts.index(self._host))

        _LOGGER.info("Custom button entity added to Home Assistant.")
        

    
    async def async_will_remove_from_hass(self):
        """Perform any actions when the button entity is removed from Home Assistant."""
        _LOGGER.info("Custom button entity removed from Home Assistant.")
    
        
    def press(self) -> None:
        _LOGGER.info("Custom button pressed.")
        pin = self._pin
        delay =self._delay
        pk.connect(self._host)
        
        pk.set_output(int(pin)-1, 1)
        
        self._inputs_updated.wait(timeout=None)
        while self._hass.data.get("host_cycle", None) != self._host:
            pass
        
        if self._inputs[self._hosts.index(self._host)][int(self._pin)-1]:
            self._state = "pressed"
    #        logging.error("pressed state")
    
        
        time.sleep(int(delay))

        pk.set_output(int(pin)-1, 0)
        
        self._inputs_updated.wait(timeout=None)
        while self._hass.data.get("host_cycle", None) != self._host:
            pass
        
        if self._inputs[self._hosts.index(self._host)][int(self._pin)-1] == False:
            self._state = "released"
    #        logging.error("relesed state")
    #pk.disconnect()
        _LOGGER.info("Custom button released.")
        

    
    async def async_turn_off(self):
        _LOGGER.info("Custom button released.")
        pk.set_output(int(pin)-1, 0)
        
        self._inputs_updated.wait()
        if self._inputs[self._hosts_index][int(pin)-1] == False:
            self._state = "released" 
            
        
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, config: ConfigType, add_entities: AddEntitiesCallBack, discovery_info=None) -> bool:
    """Set up a config entry."""
    button_component = hass.data[DOMAIN] = EntityComponent[ButtonEntity](
        logging.getLogger("pokeys"), DOMAIN, hass, SCAN_INTERVAL
    )
    await button_component.async_setup(config)

    button_component.async_register_entity_service(
        SERVICE_PRESS,
        {},
        "press",
    )

    
    component: EntityComponent[ButtonEntity] = hass.data[DOMAIN]
    return await component.async_setup_entry(entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    component: EntityComponent[ButtonEntity] = hass.data[DOMAIN]
    return await component.async_unload_entry(entry)


@dataclass
class ButtonEntityDescription(EntityDescription):


    device_class: ButtonDeviceClass | None = None


class ButtonEntity(RestoreEntity):
    """Representation of a Button entity."""

    entity_description: ButtonEntityDescription
    _attr_should_poll = False
    _attr_device_class: ButtonDeviceClass | None
    _attr_state: None = None
    __last_pressed: datetime | None = None

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
        self._inputs_updated = self._hass.data.get("inputs_updated", None)
        self._inputs = self._hass.data.get("inputs", None)
        self._hosts_index = self._hass.data.get("host_index", None)
        pk.connect(host)
        pk.set_pin_function(int(self._pin)-1, 4)
        pk.set_output(int(pin)-1, 0)

    @property
    def name(self):
        """Return the name of the button entity."""
        return self._name
        
    @property
    def icon(self):
        """Return the icon for the button entity."""
        return "mdi:gesture-double-tap"

    async def async_press(self) -> None:
        await self.hass.async_add_executor_job(self.press)
        

    def _default_to_device_class_name(self) -> bool:
        """Return True if an unnamed entity should be named by its device class.

        For buttons this is True if the entity has a device class.
        """
        return self.device_class is not None

    @property
    def device_class(self) -> ButtonDeviceClass | None:
        """Return the class of this entity."""
        if hasattr(self, "_attr_device_class"):
            return self._attr_device_class
        if hasattr(self, "entity_description"):
            return self.entity_description.device_class
        return None

    @property
    @final
    def state(self) -> str | None:
        """Return the entity state."""
        if self.__last_pressed is None:
            return None
        return self.__last_pressed.isoformat()

    @final
    async def _async_press_action(self) -> None:
        """Press the button (from e.g., service call).

        Should not be overridden, handle setting last press timestamp.
        """
        self.__last_pressed = dt_util.utcnow()
        self.async_write_ha_state()
        await self.async_press()

    async def async_internal_added_to_hass(self) -> None:
        """Call when the button is added to hass."""
        await super().async_internal_added_to_hass()
        state = await self.async_get_last_state()
        if state is not None and state.state is not None:
            self.__last_pressed = dt_util.parse_datetime(state.state)

    def press(self) -> None:
        _LOGGER.info("Custom button pressed.")
        pin = self._pin
        delay =self._delay
        
        
        
        pk.set_output(int(pin)-1, 1)
        self._inputs_updated.wait()
        #while self._host_cycle != self._host:
        #    pass
        if self._inputs[self._hosts_index][int(pin)-1]:
            self._state = "pressed"
        #    logging.error("pressedd state")
                
        time.sleep(int(delay))

        pk.set_output(int(pin)-1, 0)
                
        self._inputs_updated.wait()
#        while self._host_cycle != self._host:
#            pass
        if self._inputs[self._hosts_index][int(pin)-1] == False:
            self._state = "released"
        #    logging.error("relesed state")
        
        _LOGGER.info("Custom button released.")
