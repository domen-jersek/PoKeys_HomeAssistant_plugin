from operator import mod
import socket
import ipaddress
import struct
import random
import netifaces
import binascii
import re
import threading
from operator import add, sub
import logging

req_mutex = threading.Lock()

class pokeys_interface():
    def __init__(self):
        self.client_pk = socket.socket(2, socket.SOCK_DGRAM, socket.IPPROTO_UDP) #socket.AF_INET
        self.connected = False
        
        self.POKEYS_PORT_COM = 20055

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
        #self.client.close()
        self.client_pk.close()
        #return

    def prepare_command(self, cmdID, param1, param2, param3, param4, data, data_1):
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
        i = 8
        for d in data_1:
            req[i] = d
            i+=1
        
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
                    #print(f"Response: {response}")
                    return response
        except socket.timeout as t:
            print("Timeout - no response!")
            return None
        return None

    def get_name(self):        
        if not self.connected:
            return None

        resp = self.send_request(self.prepare_command(0x00, 0, 0, 0, 0, [], []))
        if req_mutex.locked():
            req_mutex.release()
        
        if resp != None:
            try:
                return resp[31:41].decode('UTF-8')
            except:
                return None
            
        return None
        
    def read_inputs(self):
        if not self.connected:
            return False

        resp = self.send_request(self.prepare_command(0xCC, 0, 0, 0, 0, [], []))
        if req_mutex.locked():
            req_mutex.release()

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

        resp = self.send_request(self.prepare_command(0x40, pin, 0 if state else 1, 0, 0, [], []))
        if req_mutex.locked():
            req_mutex.release()

    def set_poled_channel(self, ch, state):
        if not self.connected:
            return False

        resp = self.send_request(self.prepare_command(0xE6, 0x20, ch, state, 0, [], []))
        if req_mutex.locked():
            req_mutex.release()

    def set_pin_function(self, pin, function):
        if not self.connected:
            return False  #4=output, 2=input

        resp = self.send_request(self.prepare_command(0x10, pin, function, 0, 0, [], []))
        if req_mutex.locked():
            req_mutex.release()

    #    p = struct.pack("II", int(blind.refPos * 600000 / 100), int(blind.refAngle * 10000 / 100))
    #    resp = self.send_request_control_node(self.prepare_command(0x50, blind.ID, p))        
    
    #def stop_blind(self, blind):
    #    resp = self.send_request_control_node(self.prepare_command(0x51, blind.ID, []))   
    # 

    def read_pin_function(self, pin):
        resp = self.send_request(self.prepare_command(0x15, pin, 0, 0, 0, [], []))
        if req_mutex.locked():
            req_mutex.release()

        pinmode = list(resp[3:5])
        res = pinmode[0]

        return res #2=input, 4=output

    def get_input(self, pin):
        resp = self.send_request(self.prepare_command(0x30, pin, 0, 0, 0, [], []))
        if req_mutex.locked():
            req_mutex.release()

        state = list(resp[3:5])
        binary_state = state[0]
        if state[0] == 0:
            print("off")
        elif state[0] == 1:
            print("on")
        
        return binary_state

    def read_digital_input(self, pin):
        resp = self.send_request(self.prepare_command(0x10, pin, 2, 0, 0, [0x40], []))
        if req_mutex.locked():
            req_mutex.release()
        
        return self.get_input(pin)

    def sensor_setup(self, i):
        #self.send_request(self.prepare_command(0x60, 0, 0, 0, 0, []))
        resp = self.send_request(self.prepare_command(0x76, i, 1, 0, 0, [], []))
        if req_mutex.locked():
            req_mutex.release()
    
        return resp

    def read_sensor_values(self, i):
        resp = self.send_request(self.prepare_command(0x77, i, 1, 0, 0, [], []))
        if req_mutex.locked():
            req_mutex.release()
        
        return resp
    
    #parsed response of read_sensor_values()
    def sensor_readout(self, host, id):
        pk = pokeys_interface()
        pk.connect(host)
        i = int(id)

        packet = pk.read_sensor_values(i)
        valPacket = re.findall('..', binascii.hexlify(packet).decode())
        val_hex = str(valPacket[9])+str(valPacket[8])
        val = int(val_hex, base=16)/100
        return val

    #function that searches every web interface by sending a broadcast packet, if a pokeys device exists it responds with that device serial is used as its id
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

    def new_device_notify(self):
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

    def read_poextbus(self):
        #resp = self.send_request(self.prepare_command(0xDA, 2,0,0,0,[],[]))
        resp = self.send_request(self.prepare_command(0xDA, 2,0,0,0,[],[]))
        if req_mutex.locked():
            req_mutex.release()

        l = list(resp)
        # hex_string = ""
        # j = 0
        # for x in l:
        #     if j == 8 or j == 18: hex_string += "|"
        #     hex_string += hex(x).split("0x")[1].upper() + ","
        #     j+=1
        
        return l[8:18]#hex_string

    def poextbus_on(self, pin, host):
        pk = pokeys_interface()
        outputs = 10 *[0]
        pk.connect(host)
        outputs_state = pk.read_poextbus()
        for out_card in range(9,0,-1):
            if pin < (((9-out_card) +1)* 8) and pin > ((9-out_card)*8):
                outputs[out_card] = 1 << (pin % 8)
                out_card_n = out_card

        if pin % 8 == 0:
            outputs[pin//8] = 1
            outputs.reverse()
            out_card_n = outputs.index(1)              

        for i in range(len(outputs_state)):
            if (outputs_state[i] | outputs[i]) != outputs_state[i]:
                # Something new
                outputs_state[i] |= outputs[i]
                # send
                pk.connect(host)
                resp = self.send_request(self.prepare_command(0xDA, 1,0,0,0,[],outputs_state))
                if req_mutex.locked():
                    req_mutex.release()
                if resp != None:
                    return True
            else:
                # Nothing new
                pass


    def poextbus_off(self, pin, host):
        pk = pokeys_interface()
        outputs = 10 *[0]
        pk.connect(host)
        outputs_state = pk.read_poextbus()
        for out_card in range(9,0,-1):
            if pin < (((9-out_card) +1)* 8) and pin > ((9-out_card)*8):
                outputs[out_card] = 1 << (pin % 8)

        if pin % 8 == 0:
            outputs[pin//8] = 1
            outputs.reverse()
            
        for i in range(len(outputs_state)):

            if (outputs_state[i] & outputs[i]) != outputs_state[i]:
                # Something new
                outputs_state[i] &= ~outputs[i]
                # send
                pk.connect(host)
                resp = self.send_request(self.prepare_command(0xDA, 1,0,0,0,[],outputs_state))
                if req_mutex.locked():
                    req_mutex.release()
                if resp != None:
                    return True
            else:
                # Nothing new
                pass
        if outputs == outputs_state:
            outputs = list(map(sub, outputs_state, outputs))
            pk.connect(host)
            resp = self.send_request(self.prepare_command(0xDA, 1,0,0,0,[],outputs))
            if req_mutex.locked():
                req_mutex.release()
            if resp != None:
                    return True