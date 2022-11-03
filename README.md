# PMTR_001_CLI

#// INCLUDES / LIBRARIES / CREDITS
#//https://github.com/riptideio/pymodbus
// by riptideio

This project is based on the PZEM_004t power meter (on the server end)

This project contains firmware for the client.
The client is simply as Raspberry PI with an attached ES1642-NC module on the serial port pins, + RST pin.
Take care of using raspi-config to enable the serial port on the pins.

The main code is python script using the pymodbus library, to query one or more servers.
For now the code supports time synchronisation for the server over modbus,
fetching of power telemetry data and storing it into MariaDB, plus a crude Web display of data. The code is considered POC ok, alpha stage. 

For the server side of the project : PMTR_001_SRV

For the hardware info check the HW folder soon to be added on the client and server.
