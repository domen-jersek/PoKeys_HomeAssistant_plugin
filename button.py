from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import timedelta
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant

from pprint import pformat
from homeassistant.backports.enum import StrEnum
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.button import (PLATFORM_SCHEMA, PLATFORM_SCHEMA_BASE, ButtonEntity) 
from homeassistant.const import (CONF_NAME, CONF_PIN) 
from datetime import datetime, timedelta

from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import bind_hass
from homeassistant.util import dt as dt_util
from homeassistant.helpers.entity import EntityDescription
from homeassistant.components.button import DOMAIN
from homeassistant.core import callback

from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import EntityDescription
from typing import TypedDict, Literal, final
import time

#configuration keywords
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
#configuration schema for general button config
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_SERIAL): cv.string,
        vol.Optional(CONF_PIN): cv.string,
        vol.Optional(CONF_DELAY): cv.string,
})

async def async_setup_platform(hass: HomeAssistant, config: ConfigType, async_add_entities: AddEntitiesCallBack, discovery_info=None): #hass, config, async_add_entities, discovery_info=None
    """Set up the custom button platform."""
    component = hass.data[DOMAIN] = EntityComponent[ButtonEntity](
        logging.getLogger("pokeys"), DOMAIN, hass, SCAN_INTERVAL
    )
    #fetch buttons list from pokeys configuration
    buttons = hass.data.get("buttons", None)

    platform_run = True
    #add button entity with general configuration
    
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
    
    #add button with pokeys configuration
    
    if platform_run:
        for button in buttons:
            button = {
                "name": button[0],
                "serial": button[1],
                "pin": button[2],
                "delay": button[3],
                "entity_id": button[4]#"device_name": button[4]
            }

            async_add_entities([
                PoKeys57E(
                    hass,
                    button["entity_id"],
                    hass.data.get("instance"+str(button["serial"]), None),#get the instance of the device
                    button["name"],
                    button["serial"],
                    button["pin"],
                    button["delay"]
                )
            ])
    
    await component.async_setup(config)
    #register service of refrence entity
    component.async_register_entity_service(
        SERVICE_PRESS,
        {},
        "_async_press_action",
    )
    
    _LOGGER.info(pformat(config))

    return True


class PoKeys57E(ButtonEntity):
    def __init__(self, hass, entity_id, button_instance, name, host, pin, delay):#entity_id,
        """Initialize the button entity."""
        #self.entity_id = ENTITY_ID_FORMAT
        #self._attr_unique_id = host+".button."+name
        #self._attr_device_info = self.device_info#DeviceInfo
        self._hass = hass
        self.entity_id = "button."+entity_id
        
        self._host = host
        self._button = button_instance

        self._name = name
        self._pin = pin
        self._delay = delay
        
        self._state = "released"

    @property
    def name(self):
        """Return the name of the button entity."""
        return self._name

    def host(self):
        return self._host
        
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
        try:
            self._button.set_pin_function(int(self._pin)-1, 4)
            self._button.set_output(int(pin)-1, 0)
        except:
            pass
        #when button entity is added to HA set the configured pin as output and turn it off

        _LOGGER.info("Custom button entity added to Home Assistant.")
        
    
    async def async_will_remove_from_hass(self):
        """Perform any actions when the button entity is removed from Home Assistant."""
        _LOGGER.info("Custom button entity removed from Home Assistant.")
    
        
    def press(self) -> None:
        _LOGGER.info("Custom button pressed.")
        pin = self._pin
        delay =self._delay
        
        if int(self._pin) > 55:
            if self._button.poextbus_on(int(self._pin)-56):
                self._state = "pressed"
            else:
                logging.error("poextbus pin is alredy on")
        
            time.sleep(int(delay))
        
            if self._button.poextbus_off(int(self._pin)-56):
                self._state = "released"
            else:
                logging.error("poextbus pin is alredy off")
        
        else:
            #turn the selected pin on and listen for change of state
            if self._button.set_output(int(pin)-1, 1):
                self._state = "pressed"    
            
            time.sleep(int(delay)) #wait for selected time
            
            #turn the selected pin off and wait for change of state
            if self._button.set_output(int(pin)-1, 0):
                self._state = "released"

            _LOGGER.info("Custom button released.")

    # @property
    # def device_info(self) -> DeviceInfo:
    #     """Return the device info."""
    #     #self._attr_device_info = True
    #     self._attr_device_info = DeviceInfo(
    #         identifiers={
    #             # Serial numbers are unique identifiers within a specific domain
    #             (DOMAIN, self._attr_unique_id)
    #         },
    #         name="PoKeys",
    #         manufacturer="PoLabs d.o.o.",
    #         model="PoKeys57E",
    #         sw_version="0.1.0",
    #         #via_device=(DOMAIN, self._button),
    #     )
    #     return self._attr_device_info

# class DeviceInfo(TypedDict, total=False):
#     """Entity device information for device registry."""

#     configuration_url: str | URL | None
#     connections: set[tuple[str, str]]
#     default_manufacturer: str
#     default_model: str
#     default_name: str
#     entry_type: DeviceEntryType | None
#     identifiers: set[tuple[str, str]]
#     manufacturer: str | None
#     model: str | None
#     name: str | None
#     suggested_area: str | None
#     sw_version: str | None
#     hw_version: str | None
#     via_device: tuple[str, str]

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

    def __init__(self, hass, button_instance, name, host, pin, delay):
        """Initialize the button entity."""
        self._host = host
        self._button = button_instance

        self._hass = hass
        self._name = name
        self._pin = pin
        self._delay = delay
        
        self._state = "released"

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
        
        if int(self._pin) > 55:
            if self._button.poextbus_on(int(self._pin)-56):
                self._state = "pressed"
            else:
                logging.error("poextbus pin is alredy on")
        
            time.sleep(int(delay))
        
            if self._button.poextbus_off(int(self._pin)-56):
                self._state = "released"
            else:
                logging.error("poextbus pin is alredy off")
        
        else:
            #turn the selected pin on and listen for change of state
            if self._button.set_output(int(pin)-1, 1):
                self._state = "pressed"    
            
            time.sleep(int(delay)) #wait for selected time
            
            #turn the selected pin off and wait for change of state
            if self._button.set_output(int(pin)-1, 0):
                self._state = "released"

            _LOGGER.info("Custom button released.")