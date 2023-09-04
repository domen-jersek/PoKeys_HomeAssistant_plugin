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
import netifaces
import socket
import binascii
from typing import TypedDict
from homeassistant.components.persistent_notification import create
from homeassistant.helpers.event import async_track_time_interval
import psutil

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

def send_notification(hass: HomeAssistant, message, title):
    #creates a new notification
    create(hass, message, title)

def device_is_offline(hass: HomeAssistant, serial):
    send_notification(hass, "Configured PoKeys device "+str(serial)+" has been disconnected but still exists in your configuration which could cause issues with HomeAssistant if you wont be using it plese remove it from configuration.yaml and restart HomeAssistant", "PoKeys device disconnected")

#this function reads inputs of every pokeys device inside configuration and wirites those inputs to homeassistant
def read_inputs_update_cycle(hass: HomeAssistant, hosts, inputs_hosts, inputs_hosts_dict, serial_list):
    for host in hosts:
        
        instance = hass.data.get("instance"+str(host), None)
        if instance.read_inputs():
            inputs = instance.inputs 
            
            ind = hosts.index(host)
            inputs_hosts[ind] = inputs.copy()

            inputs_hosts_dict[host] = inputs_hosts[ind]
            hass.data["inputs"] = inputs_hosts_dict
            hass.data["host_cycle"] = host
        
        else:
            #notify homeassistant if a device goes offline
            if hass.data.get("target_host", None) != host and hass.data.get("target_host", None) != None:
                hass.data["device_offline"] = False
            ind = hosts.index(host)
            hass.data["target_host"] = host
            if hass.data.get("device_offline", None) == False:
                hass.data["device_offline"] = True
                logging.error("Configured PoKeys device "+str(serial_list[ind])+" is dead plese remove it from configuration.yaml")
                device_is_offline(hass, serial_list[ind])
                hass.data["target_host"] = None

def ping_cycle(hass: HomeAssistant, hosts, serial_list):
    for host in hosts:
        instance = hass.data.get("instance"+str(host), None)
        if instance.get_name() != False:
            pass
        else:
            #notify homeassistant if a device goes offline
            if hass.data.get("target_host", None) != host and hass.data.get("target_host", None) != None:
                hass.data["device_offline"] = False
            ind = hosts.index(host)
            hass.data["target_host"] = host
            if hass.data.get("device_offline", None) == False:
                hass.data["device_offline"] = True
                logging.error("Configured PoKeys device "+str(serial_list[ind])+" is dead plese remove it from configuration.yaml")
                device_is_offline(hass, serial_list[ind])
                hass.data["target_host"] = None

def new_device_notify():
        device_list = []
        broadcast_address = '<broadcast>'
        port = 20055
        message = b'Discovery request'
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            try:
                addresses = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addresses:
                    ipv4_addresses = addresses[netifaces.AF_INET]
                    for address_info in ipv4_addresses:
                        ip_address = address_info['addr']
                        ip_int = socket.inet_aton(ip_address).hex()
                        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        try:
                            udp_socket.bind((ip_address, 0))
                        except: socket.error
                        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                        udp_socket.sendto(message, (broadcast_address, port))
                        udp_socket.settimeout(2)
                        while True:
                            try:
                                data, address = udp_socket.recvfrom(1024)
                                serial_num_hex = binascii.hexlify(data[15:16]).decode() + binascii.hexlify(data[14:15]).decode()
                                serial_num_dec = int(serial_num_hex, 16)
                                device_list.append(serial_num_dec)
                            except socket.timeout:
                                break
                        udp_socket.close()
            except ValueError:
                pass 
        return device_list

#function that searches every web interface by sending a broadcast packet, if a pokeys device exists it responds with that device serial is used as its id
def device_discovery(serial_num_input):
    broadcast_address = '<broadcast>'
    port = 20055

    message = b'Discovery request'

    interfaces = netifaces.interfaces()
    for interface in interfaces:
        try:
            # Get the addresses for the interface
            addresses = netifaces.ifaddresses(interface)
            # Check if the interface has an IPv4 address
            if netifaces.AF_INET in addresses:
                ipv4_addresses = addresses[netifaces.AF_INET]

                for address_info in ipv4_addresses:
                    ip_address = address_info['addr']
                    ip_int = socket.inet_aton(ip_address).hex()
                    # Create a UDP socket
                    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    #print(ip_address)

                    try:
                        udp_socket.bind((ip_address, 0))
                    except: socket.error
                    
                    # Set the socket to allow broadcasting
                    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    # Send the message to the broadcast address
                    udp_socket.sendto(message, (broadcast_address, port))

                    udp_socket.settimeout(2)
                    # Listen for responses
                    while True:
                        try:
                            data, address = udp_socket.recvfrom(1024)
                            serial_num_hex = binascii.hexlify(data[15:16]).decode() + binascii.hexlify(data[14:15]).decode()
                            serial_num_dec = int(serial_num_hex, 16)
                            if str(serial_num_dec) == serial_num_input:
                                return address[0]

                        except socket.timeout:
                            break
                    
                    udp_socket.close()
                    
        except ValueError:
            pass 

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the your_integration component."""
    if DOMAIN not in config:
        return True
    
    devices = []
    hass.data["devices"] = devices
    devices_serial = []
        
    entry = config[DOMAIN]
    hass.data["device_offline"] = False

    inputs_hosts = []
    inputs_hosts_dict = {}
    serial_list = []
    #entities_devices = []

    buttons = []
    switches = []
    sensors = []
    binary_sensors = []
    hass.data["buttons"] = buttons
    hass.data["switches"] = switches
    hass.data["sensors"] = sensors
    hass.data["binary_sensors"] = binary_sensors
    
    #read the configuration tree of devices
    for device_config in entry["devices"]: 
        name = device_config["name"]
        serial = device_config["serial"]
        host = device_discovery(serial)
        inputs = []
        

        if host != None:
            #entity listing that will be passed to entity files for initialization
            
            hass.data["instance"+str(host)] = pokeys_interface(host)
            current_instance = hass.data.get("instance"+str(host), None)
            devices.append(host)
            devices_serial.append(int(serial))
            host_inputs = []
            
            inputs_hosts.append(host_inputs)
            serial_list.append(serial)

            host_inputs_2 = []
            inputs_hosts_dict["{0}".format(host)] = host_inputs_2

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
                        if current_instance.sensor_setup(0):
                            _LOGGER.info("EasySensors set up")
                        else:
                            logging.error("Sensors set up failed")
            except:
                pass

        else:
            logging.error("Device " + serial + " not avalible")
    
    #create an event loop inside  homeassistant that runs read_inputs_update_cycle every 0.5 seconds
    if len(binary_sensors)>0:
        read_inputs_update_cycle_callback = lambda now: read_inputs_update_cycle(hass, hosts=devices, inputs_hosts=inputs_hosts, inputs_hosts_dict=inputs_hosts_dict, serial_list=serial_list)
        async_track_time_interval(hass, read_inputs_update_cycle_callback, timedelta(seconds=0.5))
    else:
        ping_cycle_callback = lambda now: ping_cycle(hass, hosts=devices, serial_list=serial_list)
        async_track_time_interval(hass, ping_cycle_callback, timedelta(seconds=2))
    
    #load entity platforms
    hass.helpers.discovery.load_platform("button", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("switch", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("binary_sensor", DOMAIN, {}, config)

    #discovered devices notifications at startup
    if new_device_notify() != None:
        for device in new_device_notify():
            if (device in devices_serial) == False:
                send_notification(hass, "Discovered PoKeys device with serial number " + str(device) + " that has not been configured, to configure the device check out our blog at https://blog.poscope.com", "Found PoKeys device")
        
    return True
