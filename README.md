# PMTR_001_CLI

#// INCLUDES / LIBRARIES / CREDITS
#//https://github.com/riptideio/pymodbus
// by riptideio

This is the client side for the three phase Power Meter, Telemetry  and Relay action (PMTR)
project.

This project contains all the client code.

The client is simply as Raspberry PI with an attached ES1642-NC module on the serial port pins, + RST pin.
ES1642-NC is tied to the same phase as the server. a multi phase client is sensibgle upgrade for the future.

Take care of using raspi-config to enable the serial port on the pins.

The main code is python script using the pymodbus library, to query one or more servers.
For now the code supports time synchronisation for the server over modbus,
fetching of power telemetry data and storing it into MariaDB, plus a crude Web display of data. The code is considered POC ok, alpha stage. 

For the server side of the project : PMTR_001_SRV

For the hardware info check the HW folder soon to be added on the client and server.
