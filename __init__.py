'''pokeys57e integration'''
from __future__ import annotations
import asyncio
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from typing import Any, Protocol, cast
from dataclasses import dataclass
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_component
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity_component import *
from homeassistant.const import CONF_NAME
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
import logging
#import switch, button, binary_sensor, sensor
from .sensor import PoKeys57E as PoKeys57E_sensor
from .binary_sensor import PoKeys57E as PoKeys57E_binary_sensor
from .button import ButtonEntity as button_refrence
#from . import  switch
from homeassistant.components import button
from homeassistant.components import switch
from homeassistant.components import binary_sensor
from homeassistant.components import sensor
from custom_components.pokeys import sensor
from custom_components.pokeys import binary_sensor
from .pokeys import pokeys_instance
from .pokeys_interface import pokeys_interface
from homeassistant.helpers import entity_platform
from homeassistant.helpers import *   
from homeassistant import loader
from homeassistant import helpers
from homeassistant import components
from pprint import pformat
import time
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import bind_hass
from homeassistant.helpers.entity_platform import EntityPlatform
#from homeassistant.helpers.entity_platform import async_add_entities
from homeassistant.util import dt as dt_util
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from datetime import timedelta
from homeassistant.helpers.entity import Entity
import threading
from typing import TypedDict
from homeassistant.core import HomeAssistant
from homeassistant.components.persistent_notification import create
from homeassistant.helpers.event import async_track_time_interval
import asyncio
from .button import mutex

pk = pokeys_interface()


DOMAIN = "pokeys"
CONF_SERIAL = "serial"
CONF_PIN = "pin"
CONF_TYPE = "id"

PLATFORM_POKEYS = "pokeys"

ENTITY_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Optional("pin"): cv.string,
        vol.Optional("id"): cv.string,
        vol.Optional("delay"): cv.string,
    }
)

DEVICE_SCHEMA = vol.Schema(
    {
        vol.Optional("name"): cv.string,
        vol.Required("serial"): cv.string,
        vol.Optional("buttons"): vol.All(cv.ensure_list, [ENTITY_SCHEMA]),
        vol.Optional("switches"): vol.All(cv.ensure_list, [ENTITY_SCHEMA]),
        vol.Optional("sensors"): vol.All(cv.ensure_list, [ENTITY_SCHEMA]),
        vol.Optional("binary_sensors"): vol.All(cv.ensure_list, [ENTITY_SCHEMA]),
    }
)


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional("devices"): vol.All(cv.ensure_list, [DEVICE_SCHEMA]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


_LOGGER = logging.getLogger("pokeys")

def send_notification(hass: HomeAssistant, message):
    create(hass, message, "New PoKeys device discovered")     


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the your_integration component."""
    if DOMAIN not in config:
        return True
    
    devices = []
    
    entry = config[DOMAIN]#config[DOMAIN]
    
    global buttons
    global switches
    global sensors
    buttons = []
    switches = []
    sensors = []
    binary_sensors = []

    for device_config in entry["devices"]: #entry.data["devices"]
        name = device_config["name"]
        serial = device_config["serial"]
        host = pk.device_discovery(serial)
        if pk.connect(host):
            try:
                for entity_config in device_config["buttons"]:
                    name_button = entity_config["name"]
                    pin_button = entity_config["pin"]
                    delay_button = entity_config["delay"]
                    
                    entity_button = [name_button, serial, pin_button, delay_button]
                    buttons.append(entity_button)
                    
            except:
                pass
            try:
                for entity_config in device_config["switches"]:
                    name_switch = entity_config["name"]
                    pin_switch = entity_config["pin"]

                    entity_switch = [name_switch, serial, pin_switch]
                    switches.append(entity_switch)
                    
            except:
                pass
            try:
                for entity_config in device_config["binary_sensors"]:
                    name_binary_sensor = entity_config["name"]
                    pin_binary_sensor = entity_config["pin"]

                    entity_binary_sensor = [name_binary_sensor, serial, pin_binary_sensor]
                    binary_sensors.append(entity_binary_sensor)

                    await async_setup_platform_binary_sensor(hass, config, AddEntitiesCallback, entity_binary_sensor, discovery_info=None)
            except:
                pass
            try:
                for entity_config in device_config["sensors"]:
                    name_sensor = entity_config["name"]
                    type_sensor = entity_config["id"]

                    entity_sensor = [name_sensor, serial, type_sensor]
                    sensors.append(entity_sensor)

                    #await async_setup_platform_sensor(hass, config, AddEntitiesCallback, entity_sensor, discovery_info=None)
            except:
                pass
            
            async_track_time_interval(hass, read_inputs_update_cycle, timedelta(seconds=1))
            #read_inputs_thread = threading.Thread(target=read_inputs_update_cycle)
            #read_inputs_thread.start()
        
        else:
            logging.error("Device " + serial + " not avalible")

    hass.helpers.discovery.load_platform("button", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("switch", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)

    if pk.new_device_notify() != None:
        send_notification(hass, "Discovered PoKeys device with serial number " + str(pk.new_device_notify()))
        
    
        
    return True

    
def read_inputs_update_cycle(self):
    
    pk.read_inputs()
    global inputs
    inputs = pk.inputs
    
    if mutex.locked():
        logging.error(time.time())
        mutex.release()
    
        

async def async_setup_platform_binary_sensor(hass: HomeAssistant, config: ConfigType, async_add_entities: AddEntitiesCallback, binary_sensor, discovery_info=None) -> bool:
    await EntityPlatform(hass=hass, logger=_LOGGER, domain="binary_sensor", platform_name="pokeys", platform=pokeys, scan_interval=timedelta(seconds=8), entity_namespace=None).async_add_entities([PoKeys57E_binary_sensor(hass, binary_sensor[0], binary_sensor[1], binary_sensor[2])]) 

#async def async_setup_platform_sensor(hass: HomeAssistant, config: ConfigType, async_add_entities: AddEntitiesCallback, sensor, discovery_info=None) -> bool:
#    await EntityPlatform(hass=hass, logger=_LOGGER, domain="sensor", platform_name="pokeys", platform=pokeys, scan_interval=timedelta(seconds=8), entity_namespace=None).async_add_entities([PoKeys57E_sensor(hass, sensor[0], sensor[1], sensor[2])]) 

