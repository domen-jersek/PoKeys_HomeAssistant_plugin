'''pokeys integration'''
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

from homeassistant.components import button
from homeassistant.components import switch
from homeassistant.components import binary_sensor
from homeassistant.components import sensor
#from custom_components.pokeys import sensor
#from custom_components.pokeys import binary_sensor
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
from functools import partial


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

inputs_updated = threading.Event()
send_recive = threading.Event()


def send_notification(hass: HomeAssistant, message):
    create(hass, message, "New PoKeys device discovered")     


def read_inputs_update_cycle(hass: HomeAssistant, inputs, hosts, inputs_hosts):

    for host in hosts:
        #logging.error(hosts.index(host))
        
        pk.connect(host)

        pk.read_inputs()

        inputs =pk.inputs 
        
        #logging.error(host)
        #logging.error(inputs)
        ind = hosts.index(host)
        inputs_hosts[ind] = inputs.copy()

        hass.data["inputs"] = inputs_hosts
        hass.data["hosts"] = hosts
        hass.data["host_cycle"] = host
        
        
        #inputs_hosts[hosts.index(host)] = inputs
        #logging.error(inputs_hosts)
                #if ind == hosts.index(host):
    #    if len(inputs_hosts[host])==0:
    #        inputs_hosts[host].append(inputs)
    #    else:
    #        inputs_hosts[host][0] = inputs
        #if inputs_hosts[host] == host
    #      logging.error(hosts.index(host))
    #      logging.error(inputs)
        #if len(inputs_hosts)<len(hosts):
            
        #inputs_hosts[ind].append(inputs)
        #else:
        #inputs_hosts = inputs_hosts[:ind]+[inputs]+inputs_hosts[ind+1:]
        
        #if len(inputs_hosts[host])==0:
        
        #    inputs_hosts[str(host)].append(inputs)
        #else:

        #    inputs_hosts[str(host)] = inputs
        #inputs_hosts[host].append(inputs)
        #inputs_hosts[str(host)] = inputs #[hosts.index(host)]
       # logging.error(host)
    #    logging.error(ind)
       # logging.error(hosts.index(host))
    #    logging.error(inputs_hosts[host])
       # logging.error(inputs_hosts)
        
        #logging.error(inputs_hosts[str(host)][0])
        #logging.error(inputs_hosts["192.168.1.177"])
        #inputs_hosts[hosts].remove(inputs)
        #other_host = hosts[hosts.index(host)-1]
        #if len(inputs_hosts[str(host)]) != 0:
  #      logging.error(hosts[hosts.index(host)-1])
        #pk.connect(hosts[hosts.index(host)-1])
        if inputs != None:
            inputs_updated.set()
            inputs_updated.clear()
        #inputs_hosts[ind].remove(inputs)
        

"""def read_sensor_cycle(hass: HomeAssistant, devices, sensors, serial, sensors_list, id_list):
    
    for host in devices:
        if serial in sensors:
        for id in id_list:
            if len(id_list)>len(sensors_list):
                val = pk.sensor_readout(hass, host, id)
                sensors_list.append(val)
                logging.error(sensors_list)
            else:
                val = pk.sensor_readout(hass, host, id)
                sensors_list[id] = val
                logging.error(sensors_list)
"""


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the your_integration component."""
    if DOMAIN not in config:
        return True
    
    devices = []
    hass.data["devices"] = devices
    hass.data["send_recive"] = send_recive
    
    entry = config[DOMAIN]
    hass.data["inputs_updated"] = inputs_updated

    inputs_hosts = []    

    buttons = []
    switches = []
    sensors = []
    binary_sensors = []
    hass.data["buttons"] = buttons
    hass.data["switches"] = switches
    hass.data["sensors"] = sensors
    hass.data["binary_sensors"] = binary_sensors
    
    for device_config in entry["devices"]: 
        name = device_config["name"]
        serial = device_config["serial"]
        host = pk.device_discovery(serial)
        inputs = []

        

        if pk.connect(host):

            devices.append(host)
            host_inputs = []
            #inputs_hosts["{0}".format(host)] = host_inputs
            inputs_hosts.append(host_inputs)

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

            except:
                pass
            try:
                for entity_config in device_config["sensors"]:
                    
                    name_sensor = entity_config["name"]
                    type_sensor = entity_config["id"]
                
                    #id_list.append(int(type_sensor))
                    
                    entity_sensor = [name_sensor, serial, type_sensor]
                    sensors.append(entity_sensor)

            except:
                pass
        
            try:
                if (len(entity_sensor) > 0):
                        send_recive.set()
                        if pk.sensor_setup(hass, 0):
                            _LOGGER.info("Sensors set up")
                            #logging.error("sensor set up")
                            send_recive.clear()
                        else:
                            logging.error("Sensors set up failed")
            except:
                pass        
        
        else:
            logging.error("Device " + serial + " not avalible")
        
        
        #if len(sensors)>0:
        #    read_sensor_cycle_callback = lambda now: read_sensor_cycle(hass, devices=devices, serial=serial, sensors=sensors, sensors_list=sensors_list, id_list=id_list)
        #    async_track_time_interval(hass, read_sensor_cycle_callback, timedelta(seconds=1))


    read_inputs_update_cycle_callback = lambda now: read_inputs_update_cycle(hass, inputs=inputs, hosts=devices, inputs_hosts=inputs_hosts)
    #read_inputs_update_cycle_dict["read_inputs_update_cycle_callback_" + str(serial)]
    async_track_time_interval(hass, read_inputs_update_cycle_callback, timedelta(seconds=2))

    hass.helpers.discovery.load_platform("button", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("switch", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("binary_sensor", DOMAIN, {}, config)

    if pk.new_device_notify() != None:
        send_notification(hass, "Discovered PoKeys device with serial number " + str(pk.new_device_notify()))
        
    
        
    return True
