import asyncio
import logging
from homeassistant.const import (CONF_NAME) #, CONF_SERIAL
from .pokeys_interface import pokeys_interface

pk = pokeys_interface()
LOGGER = logging.getLogger(__name__)
CONF_SERIAL = "serial"

class pokeys_instance:
    def __init__(self, serial: str):
        self._serial = serial
        host = pk.device_discovery(serial)
        self._device = pk.connect(host)
        self._is_on = None
        self._connected = None

    async def _send(self):
        host = pk.device_discovery(_serial)
        if not pk.connect(host):
            LOGGER.error("Not available")
        else:
            LOGGER.error("Device name " + pk.get_name())
            LOGGER.error(pk.inputs)

    def serial(self):
        return self._serial
    
    def is_on(self):
        return self._is_on
    
