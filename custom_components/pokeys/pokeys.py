import logging
import socket
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from .pokeys_interface import pokeys_interface


LOGGER = logging.getLogger(__name__)
CONF_HOST = "host"

class pokeys_instance:
    #device instance
    def __init__(self, host: str): 
        self.pk = pokeys_interface()
        self._host = host
        self.POKEYS_PORT_COM = 20055
        self.client_pk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) #socket.AF_INET  2
        self.connected = False
        self._device = self.connect(host)
        self._is_on = None
        
    async def _send(self):
        
        if not self.pk.connect(host):
            logging.error("Not available")
        else:
            logging.error("Device name " + self.pk.get_name())
            self.pk.read_inputs()
            logging.error(self.pk.inputs)

    def host(self):
        logging.error(self._host)
        return self._host
    
    def unique_id(self):
        return "pokeys."+self._name

    def connected(self):
        if self.connected:
            logging.error("connected "+self._host)
        else:
            logging.error("not connected")

    def is_on(self):
        return self._is_on

    def connect(self, host):
        
        logging.error(str(self._host)+"connecting...")
        if host == None:
            return False
        self.client_pk.connect((host, self.POKEYS_PORT_COM))
        self.client_pk.settimeout(1)
        self.connected = True
        logging.error(self.connected)
        return self.connected
    
    def name(self):
        return self._name

