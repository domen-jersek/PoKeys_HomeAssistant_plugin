from operator import mod
import socket
import ipaddress
import struct
import random
#from netifaces import interfaces, ifaddresses, AF_INET

class pokeys_interface():
    def __init__(self):
        self.client_pk = socket.socket(2, socket.SOCK_DGRAM, socket.IPPROTO_UDP) #socket.AF_INET
        self.connected = False
        
        self.POKEYS_PORT_COM = 20055
        self.address = "192.168.0.104"       

        self.users = []
        self.blinds = dict()
        
        self.requestID = random.randint(0, 255)

        self.inputs = [False] * 55

    def connect(self, address):
        if address == None:
            return False
        print("Connecting to " + address)
        self.client_pk.connect((address, self.POKEYS_PORT_COM))
        self.client_pk.settimeout(1)
        self.connected = True
        return self.read_inputs()

    def disconnect(self):
        self.client.close()
        self.client_pk.close()
        return

    def prepare_command(self, cmdID, param1, param2, param3, param4, data):
        self.requestID = (self.requestID + 1) % 256

        req = bytearray(64)
        req[0] = 0xBB
        req[1] = cmdID
        req[2] = param1
        req[3] = param2
        req[4] = param3
        req[5] = param4
        req[6] = self.requestID
        req[7] = sum(req[0:7]) % 256
        
        l = len(data)
        if l > 0:
            req[8:8+l] = bytearray(data)
        return req

    def send_request(self, command):
        if not self.connected:
            return None
        try:
            for rety in range(3):
                #print(f"Request: {command}")
                self.client_pk.sendall(bytes(command))            
                response = self.client_pk.recv(1024)
                if response[6] == command[6]:
                    #print(f"Response: {response}")
                    return response
        except socket.timeout as t:
            print("Timeout - no response!")
            return None
        return None

    def get_name(self):        
        if not self.connected:
            return None

        resp = self.send_request(self.prepare_command(0x00, 0, 0, 0, 0, []))
        if resp != None:
            try:
                return resp[31:41].decode('UTF-8')
            except:
                return None
            
        return None
        
    def read_inputs(self):
        if not self.connected:
            return False

        resp = self.send_request(self.prepare_command(0xCC, 0, 0, 0, 0, []))
        if resp != None:
            try:
                # Parse the response
                for i in range(55):
                    self.inputs[i] = (resp[8 + int(i / 8)] & (1 << (mod(i, 8)))) > 0
                return True
            except:
                return False
            
        return False   

    def set_output(self, pin, state):
        if not self.connected:
            return False

        resp = self.send_request(self.prepare_command(0x40, pin, 0 if state else 1, 0, 0, []))

    def set_poled_channel(self, ch, state):
        if not self.connected:
            return False

        resp = self.send_request(self.prepare_command(0xE6, 0x20, ch, state, 0, []))

    def set_pin_function(self, pin, function):
        if not self.connected:
            return False  #2=output, 4=input

        resp = self.send_request(self.prepare_command(0x10, pin, function, 0, 0, []))
    #    p = struct.pack("II", int(blind.refPos * 600000 / 100), int(blind.refAngle * 10000 / 100))
    #    resp = self.send_request_control_node(self.prepare_command(0x50, blind.ID, p))        
    
    #def stop_blind(self, blind):
    #    resp = self.send_request_control_node(self.prepare_command(0x51, blind.ID, []))   
    # 

    def read_pin_function(self, pin):
        resp = self.send_request(self.prepare_command(0x15, pin, 0, 0, 0, []))
        
        pinmode = list(resp[3:5])
        res = pinmode[0]
        '''if pinmode[0] == 2:
            print("input")
            res = 0
        elif pinmode[0] == 4:
            print("output")
            res = 1'''
        return res

    def get_input(self, pin):
        resp = self.send_request(self.prepare_command(0x30, pin, 0, 0, 0, []))
        
        state = list(resp[3:5])
        binary_state = state[0]
        if state[0] == 0:
            print("off")
        elif state[0] == 1:
            print("on")
        
        return binary_state

    def read_digital_input(self, pin):
        resp = self.send_request(self.prepare_command(0x10, pin, 2, 0, 0, []))
        return self.get_input(pin)   


if __name__ == "__main__":
    # Test the interface
    print("PoKeys interface test...")
    pk = pokeys_interface()
    if not pk.connect("192.168.0.104"):
        print("Not available")
    else:
        print("Device name " + pk.get_name())
        print(pk.inputs)
        #pk.send_request(pk.prepare_command(0x40, 12, 0 if False else 1, 0, 0, []))
        print("done")

