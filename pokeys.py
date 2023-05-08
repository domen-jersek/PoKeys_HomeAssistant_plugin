import asyncio
import logging
from homeassistant.const import (CONF_NAME, CONF_HOST)
from .pokeys_interface import pokeys_interface

pk = pokeys_interface()
LOGGER = logging.getLogger(__name__)

class pokeys_instance:
    def __init__(self, host: str):
        self._host = host
        self._device = pk.connect(host)
        self._is_on = None
        self._connected = None

    async def _send(self):
        if not pk.connect(_host):
            LOGGER.error("Not available")
        else:
            LOGGER.error("Device name " + pk.get_name())
            LOGGER.error(pk.inputs)

    def host(self):
        return self._host
    
    def is_on(self):
        return self._is_on
    
#pokeys_instance("192.168.1.10")
