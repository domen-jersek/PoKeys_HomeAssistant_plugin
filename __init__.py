'''pokeys integration'''
from __future__ import annotations
import asyncio
import voluptuous as vol
from typing import Any, Protocol, cast
from dataclasses import dataclass
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
import logging
from homeassistant.components import button
from homeassistant.components import switch
from homeassistant.components import binary_sensor
from homeassistant.components import sensor
from .pokeys import pokeys_instance
from .pokeys_interface import pokeys_interface
from pprint import pformat
from homeassistant.loader import bind_hass
from homeassistant.util import dt as dt_util
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from datetime import timedelta
import threading

from typing import TypedDict
from homeassistant.components.persistent_notification import create
from homeassistant.helpers.event import async_track_time_interval
import psutil


pk = pokeys_interface()

#keywords in config
DOMAIN = "pokeys"
CONF_SERIAL = "serial"
CONF_PIN = "pin"
CONF_TYPE = "id"

#each entity list contains name of the entity and the parameters it requiers
ENTITY_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Optional("pin"): cv.string,
        vol.Optional("id"): cv.string,
        vol.Optional("delay"): cv.string,
    }
)

#devices schema includes device name, device serial and lists of entities 
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
            {#pokeys has one option(devices)
                vol.Optional("devices"): vol.All(cv.ensure_list, [DEVICE_SCHEMA]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


_LOGGER = logging.getLogger("pokeys")

#threading event acting as mutex to prevent skipping updated states
inputs_updated = threading.Event()


def send_notification(hass: HomeAssistant, message):
    #creates a new notification with title "Found PoKeys device"
    create(hass, message, "Found PoKeys device")     

#this function reads inputs of every pokeys device inside configuration and wirites those inputs to homeassistant
def read_inputs_update_cycle(hass: HomeAssistant, inputs, hosts, inputs_hosts, inputs_hosts_dict):
    for host in hosts:
        
        pk.connect(host)
        if pk.read_inputs():
            inputs =pk.inputs 
            
            ind = hosts.index(host)
            inputs_hosts[ind] = inputs.copy()

            inputs_hosts_dict[host] = inputs_hosts[ind]
            hass.data["inputs"] = inputs_hosts_dict
            hass.data["host_cycle"] = host

            
            inputs_updated.set()
            inputs_updated.clear()
        else:
            logging.error("configured pokeys device not found")

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the your_integration component."""
    if DOMAIN not in config:
        return True
    
    devices = []
    hass.data["devices"] = devices
    devices_serial = []
        
    entry = config[DOMAIN]
    hass.data["inputs_updated"] = inputs_updated

    inputs_hosts = []
    inputs_hosts_dict = {}
    serial_list = []
    device_sockets = {}

    buttons = []
    switches = []
    sensors = []
    binary_sensors = []
    hass.data["buttons"] = buttons
    hass.data["switches"] = switches
    hass.data["sensors"] = sensors
    hass.data["binary_sensors"] = binary_sensors

    hass.data["connect"] = pk.connect
    
    #read the configuration tree of devices
    for device_config in entry["devices"]: 
        name = device_config["name"]
        serial = device_config["serial"]
        host = pk.device_discovery(serial)
        inputs = []
        

        if pk.connect(host):
            #entity listing that will be passed to entity files for initialization
            devices.append(host)
            devices_serial.append(int(serial))
            host_inputs = []
            
            inputs_hosts.append(host_inputs)
            serial_list.append(serial)

            host_inputs_2 = []
            inputs_hosts_dict["{0}".format(host)] = host_inputs_2
            #inputs_hosts_2.append(host_inputs_2)

            try:
                for entity_config in device_config["buttons"]:
                    name_button = entity_config["name"]
                    pin_button = entity_config["pin"]
                    delay_button = entity_config["delay"]
                    
                    entity_button = [name_button, host, pin_button, delay_button]
                    buttons.append(entity_button)
                    
            except:
                pass
            try:
                for entity_config in device_config["switches"]:
                    name_switch = entity_config["name"]
                    pin_switch = entity_config["pin"]

                    entity_switch = [name_switch, host, pin_switch]
                    switches.append(entity_switch)
                    
            except:
                pass
            try:
                for entity_config in device_config["binary_sensors"]:
                    name_binary_sensor = entity_config["name"]
                    pin_binary_sensor = entity_config["pin"]

                    entity_binary_sensor = [name_binary_sensor, host, pin_binary_sensor]
                    binary_sensors.append(entity_binary_sensor)

            except:
                pass
            try:
                for entity_config in device_config["sensors"]:
                    
                    name_sensor = entity_config["name"]
                    type_sensor = entity_config["id"]
                    
                    entity_sensor = [name_sensor, host, type_sensor]
                    sensors.append(entity_sensor)

            except:
                pass
            
            #EasySensor setup
            try:
                if (len(entity_sensor) > 0):
                        if pk.sensor_setup(0):
                            _LOGGER.info("EasySensors set up")
                        else:
                            logging.error("Sensors set up failed")
            except:
                pass
        
        else:
            logging.error("Device " + serial + " not avalible")

    
    #create an event loop inside  homeassistant that runs read_inputs_update_cycle every 2 seconds
    read_inputs_update_cycle_callback = lambda now: read_inputs_update_cycle(hass, inputs=inputs, hosts=devices, inputs_hosts=inputs_hosts, inputs_hosts_dict=inputs_hosts_dict)
    async_track_time_interval(hass, read_inputs_update_cycle_callback, timedelta(seconds=0.5))

    #load entity platforms
    hass.helpers.discovery.load_platform("button", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("switch", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("binary_sensor", DOMAIN, {}, config)

    #discovered devices notifications at startup
    if pk.new_device_notify() != None:
        for device in pk.new_device_notify():
            if (device in devices_serial) == False:
                send_notification(hass, "Discovered PoKeys device with serial number " + str(device))
        
    return True
