from __future__ import annotations
from operator import mod
import socket
import ipaddress
import struct
import random
import netifaces
import binascii
import re
import threading

req_mutex = threading.Lock()

class pokeys_interface():
    def __init__(self):
        self.client_pk = socket.socket(2, socket.SOCK_DGRAM, socket.IPPROTO_UDP) #socket.AF_INET
        self.connected = False
        
        self.POKEYS_PORT_COM = 20055
        self.address = "192.168.1.177"       

        self.users = []
        self.blinds = dict()
        
        self.requestID = random.randint(0, 255)

        self.inputs = [False] * 55

    def connect(self, address):
        if address == None:
            return False
        #print("Connecting to " + address)
        self.client_pk.connect((address, self.POKEYS_PORT_COM))
        self.client_pk.settimeout(1)
        self.connected = True
        return self.connected
        #return self.read_inputs()

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
                req_mutex.acquire()
                response = self.client_pk.recv(1024)
                
                if response[6] == command[6]:
                    #req_mutex.wait()
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
        if req_mutex.locked():
            req_mutex.release()
        
        #req_mutex.clear()
        
        #req_mutex.release()
        #req_mutex.clear()
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
        if req_mutex.locked():
            req_mutex.release()
        
        #req_mutex.clear()
        #req_mutex.release()
        if resp != None:
            try:
                # Parse the response
                for i in range(55):
                    self.inputs[i] = (resp[8 + int(i / 8)] & (1 << (mod(i, 8)))) > 0
                return True
                #reading(HomeAssistant)
                #inputs_read.set()
                #inputs_read.clear()
            except:
                return False
            
        return False   

    def set_output(self, pin, state):
        if not self.connected:
            return False

        resp = self.send_request(self.prepare_command(0x40, pin, 0 if state else 1, 0, 0, []))
        if req_mutex.locked():
            req_mutex.release()
        
        #req_mutex.clear()
        #req_mutex.release()

    def set_poled_channel(self, ch, state):
        if not self.connected:
            return False

        resp = self.send_request(self.prepare_command(0xE6, 0x20, ch, state, 0, []))
        if req_mutex.locked():
            req_mutex.release()
        
        #req_mutex.clear()
        #req_mutex.release()

    def set_pin_function(self, pin, function):
        if not self.connected:
            return False  #2=output, 4=input

        resp = self.send_request(self.prepare_command(0x10, pin, function, 0, 0, []))
        if req_mutex.locked():
            req_mutex.release()
        
        #req_mutex.clear()
        #req_mutex.release()
    #    p = struct.pack("II", int(blind.refPos * 600000 / 100), int(blind.refAngle * 10000 / 100))
    #    resp = self.send_request_control_node(self.prepare_command(0x50, blind.ID, p))        
    
    #def stop_blind(self, blind):
    #    resp = self.send_request_control_node(self.prepare_command(0x51, blind.ID, []))   
    # 

    def read_pin_function(self, pin):
        resp = self.send_request(self.prepare_command(0x15, pin, 0, 0, 0, []))
        if req_mutex.locked():
            req_mutex.release()
        
        #req_mutex.clear()
        #req_mutex.release()

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
        if req_mutex.locked():
            req_mutex.release()
        
        #req_mutex.clear()
        #req_mutex.release()
        state = list(resp[3:5])
        binary_state = state[0]
        if state[0] == 0:
            print("off")
        elif state[0] == 1:
            print("on")
        
        return binary_state

    def read_digital_input(self, pin):
        resp = self.send_request(self.prepare_command(0x10, pin, 2, 0, 0, [0x40]))
        if req_mutex.locked():
            req_mutex.release()
        
        #req_mutex.clear()
        #req_mutex.release()
        return self.get_input(pin)

    def sensor_setup(self, hass, i):
        #self.send_request(self.prepare_command(0x60, 0, 0, 0, 0, []))
        send_recive = hass.data.get("send_recive", None)
        resp = self.send_request(self.prepare_command(0x76, i, 1, 0, 0, []))
        if req_mutex.locked():
            req_mutex.release()
        
        #req_mutex.clear()
        #req_mutex.release()
        send_recive.wait()
        return resp

    def read_sensor_values(self,hass, i):
        #send_recive = hass.data.get("send_recive", None)
        resp = self.send_request(self.prepare_command(0x77, i, 1, 0, 0, [])) #, 0, 1, 0, []
        if req_mutex.locked():
            req_mutex.release()
        
        #req_mutex.clear()
        #req_mutex.release()
        #send_recive.wait()
        return resp
    
    
    def sensor_readout(self, hass, host, id):
        pk = pokeys_interface()
        #host = pk.device_discovery(serial)
        pk.connect(host)
        i = int(id)
        
        #config = re.findall('..', binascii.hexlify(pk.sensor_setup(i)).decode())
        packet = pk.read_sensor_values(hass, i)
        valPacket = re.findall('..', binascii.hexlify(packet).decode())
        val_hex = str(valPacket[9])+str(valPacket[8])
        val = int(val_hex, base=16)/100
        return val

    def device_discovery(self, serial_num_input):
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
                        print(ip_address)

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
                                #print(binascii.hexlify(data).decode())
                                serial_num_hex = binascii.hexlify(data[15:16]).decode() + binascii.hexlify(data[14:15]).decode()
                                serial_num_dec = int(serial_num_hex, 16)
                                print(serial_num_dec)
                                print(address[0])
                                print(f"Received response from {address}: {data}")
                                if str(serial_num_dec) == serial_num_input:
                                    print(address[0])
                                    return address[0]
                                    
                                else:
                                    print("No device found")

                            except socket.timeout:
                                print("No more responses")
                                break
                        
                        udp_socket.close()
                        
            except ValueError:
                pass 

    def new_device_notify(self):
        
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
                                return serial_num_dec
                            except socket.timeout:
                                break
                        udp_socket.close()          
            except ValueError:
                pass 
            

#if __name__ == "__main__":
    # Test the interface
#    print("PoKeys interface test...")
#    pk = pokeys_interface()
#    host = pk.device_discovery("31557")
#    if not pk.connect(host):
#        print("Not available")
#    else:
#        print("Device name " + pk.get_name())
#        print(pk.inputs)
#        print(pk.sensor_readout())
#        print("done")

