# PMTR_001_CLI

This project is based on the PZEM_004t power meter (on the server end)

This project contains firmware for the client.
On the hardware side, it uses an Arduino Mega2560, a ES-1642 power line communication modem on the HardwareSerial1 pins, a SPI memory flash device to store the servers data.

As per Modbus RS485 protocol mode of operation, it regularly polls all the servers on the bus, interrogating coils & registers.

It then stores the data on the flash memory unit, and after each cycle of polling uploads the data to computerized system that will manage all telemetry.

This could be done using an Ethernet or Wifi hardware layer.
As of the software layer, in the current advancement of the project, it is not yet decided what kind of method will be used. Probably an IoT specific protocol like MQTT.

Proof of Concept.

As of August 2022, the following has been tested as working :

A single server and a Single client connected over a mains energized 20 meters of 1.5 mm2 power line cable, with over one hour of polling, yielding to a 0% failure rate of transmission. (using two ES-1642 plc modems modules, on the client and server side)

All data made available by the PZEM-004t have been dispatched into Modbus registers. As they are float values, a pair of 16 bit registers store the whole float value. a memcpy operation then populates the float value from the pair of uint16_t memory addresses.

Slight changes have been made to the RS485 Arduino libraries. Please keep that in mind.

What's next ?

We need to test the setup with more than one server on the bus, ideally in a real world setup (on existing local power infrastructure)

Keep in mind that the signal will not cross the utility power meter into utility network, it will only be available inside the premises.
Also, the signal will not cross EMI filters or will be severly attenuated.
A rough measure using an oscilloscope shows the signal using a 3.6 Mhz carrier.
The module datasheet indicates a bps rate of between 2.5 to 4.5 kbps

Next, device scanning is to be tested, to narrow the number of clients to be interrogated at each cycle, and excluded absent addresses. The modbus RS485 protocol allows up to 256 servers.
