import logging
from homeassistant.const import CONF_NAME
from .pokeys_interface import pokeys_interface

pk = pokeys_interface()
LOGGER = logging.getLogger(__name__)
CONF_HOST = "host"

class pokeys_instance:
    #device instance
    def __init__(self, host: str):
        self._host = host
        self._device = pk.connect(host)
        self._is_on = None
        self._connected = None

    async def _send(self):
        host = pk.device_discovery(_serial)
        if not pk.connect(host):
            logging.error("Not available")
        else:
            logging.error("Device name " + pk.get_name())
            logging.error(pk.inputs)

    def serial(self):
        return self._serial
    
    def is_on(self):
        return self._is_on
    