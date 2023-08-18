# PoKeys_HomeAssistant_plugin

A HomeAssistant plugin for the PoKeys57E Ethernet I/O controller that contains all of the basic features required for most home automation projects.

# Setup

- Go to your HomeAssistant config folder and create a folder called custom_components
- In the custom_components folder create a folder called pokeys
- Simply copy the repo into your pokeys folder
- Restart HomeAssistant
- After restart you can now add your pokeys device to the file configuration.yaml
- An example of the pokeys configuration inside configuration.yaml:

```
#pokeys configuration example
pokeys:
  devices:
    - name: "PoKeys57E_device_1"
      serial: 31557 #the serial number of your pokeys device
      buttons:
        - name: "pokeys_button_1" #the name of your button entity
          pin: 13 #the pin that will be efected
          delay: 4 #describes how long(seconds) the button will be turned on after press is called
        - name: "pokeys_button_2"
          pin: 12
          delay: 2

      binary_sensors:
        - name: "pokeys_binary_sensor"
          pin: 8

    - name: "PoKeys57E_device_2"
      serial: 31708
      sensors:
        - name: "pokeys_easy_sensor_temperature"
          id: 0 #sensor id/index

      switches:
        - name: "pokeys_switch"
          pin: 12

#supported entities: switch, button, sensor(for pokeys EasySensor), binary_sensor
```

- After adding the pokeys configuration for your home automation project restart HomeAssistant and the entities you inputed will be added to HomeAssistant
- When setting up output entities note that the pins 56-136 are reserved for PoExtBus in a counting fashion
