import pymodbus
import pymysql
import argparse
import os
import logging
import time
import struct
import math
#--------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
#    ModbusTcpClient,
#    ModbusTlsClient,
#    ModbusUdpClient,
#)
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
#from pymodbus.transaction import (
#    ModbusAsciiFramer,
#    ModbusBinaryFramer,
#    ModbusRtuFramer,
#    ModbusSocketFramer,
#    ModbusTlsFramer,
#)

def insert(epoch,L1_voltage_V,L1_current_A,L1_active_power_W,L1_energy_kWh,L1_frequency_Hz,L1_pf):
    # Create a connection object
    # IP address of the MySQL database server
    Host = "localhost"  
    # User name of the database server
    User = "pmtr_user"       
    # Password for the database user
    Password = "password"           
  
    database = "PMTR"
    epoch = round(epoch)
  
    conn  = pymysql.connect(host=Host, user=User, password=Password, db=database)

    # Create a cursor object
    cur  = conn.cursor()

    params = [L1_voltage_V,
              L1_current_A,
              L1_active_power_W,
              L1_energy_kWh,
              L1_frequency_Hz,
              L1_pf]
  
    cur.execute("INSERT INTO instant VALUES(NOW(), %s, DEFAULT, DEFAULT, %s, DEFAULT, DEFAULT, %s, DEFAULT, DEFAULT, %s, DEFAULT, DEFAULT, %s, DEFAULT, DEFAULT, %s, DEFAULT, DEFAULT)", params) 
    print(f"{cur.rowcount} details inserted")
    conn.commit()
    conn.close()


client = ModbusClient(port="/dev/ttyS0",method="rtu",baudrate=9600,bytesize=8,parity="N",stopbits=1, timeout=5, retries=10, retry_on_empty=False, strict=False)  # serial port

connection = client.connect()
print(connection)
# Common optional paramers:
#    method='rtu',
#    framer='rtu',
#    timeout=10,
#    retries=3,
#    retry_on_empty=False,
#    close_comm_on_error=False,.
#    strict=True,
# Serial setup parameters
#    baudrate=9600,
#    bytesize=8,
#    parity="N",
#    stopbits=1,
#    handle_local_echo=False,
#    )

UNIT = 0x01
BROADCAST = 0x0
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

rq = client.write_coil(0,True,unit=BROADCAST)
print("error: {}".format(rq))
time.sleep(1)

builder = BinaryPayloadBuilder(byteorder=Endian.Big,wordorder=Endian.Little)
timeseconds = math.floor(time.time())
timemilliseconds = math.floor(1000*(timeseconds % 1))
builder.add_64bit_uint(timeseconds)
builder.add_16bit_uint(timemilliseconds)
payload = builder.build()
epochregisters = builder.to_registers()

rq = client.write_registers(146,epochregisters,unit=BROADCAST)
print("epoch registers sent")
print("error: {}".format(rq))
time.sleep(1)
rq = client.write_coil(0,False,unit=BROADCAST)

time.sleep(1)
#Sending a Formula

# coil 1 : formula update requested by client
  # coil 2 : formula digitalwrite HIGH or LOW on formula evaluation returning true
  # coil 3 : formula DRY RUN : does not effect pin status, only reports it (see pin statuses coils)
  # coil 4 : trip recovery strategy, MANUAL or AUTO on condition clear


  # HOLDING REGISTERS FOR TRIP FORMULAS UPDATE
  # holding register 28 LSB : MA Window in seconds to use for formula evaluation of variables. all variables in the same formula
  # are evaluated using the same MA Windows
  # holding register 28 MSB : Formula Slot that is being updated
  # holding register 29 to 32 : list of pins to trip. each register holds 2 list items (8 bit pin ID). max number of pins : 8  
  # holding register 33 : trip recovery hysteresis time : duration in seconds condition must remain clear before
  # pin(s) reactivation if AUTO MODE.
  # holding registers 34 to 65 : formula string

#rq = client.write_coil(1,True,unit=BROADCAST) # advertising a formula update
rq = client.write_coils(2,[False,False,True],unit=UNIT) # writing formula coils

print("error: {}".format(rq))
time.sleep(1)

builder = BinaryPayloadBuilder(byteorder=Endian.Big,wordorder=Endian.Little)
builder.add_8bit_uint(5) # MA Window 5 seconds
builder.add_8bit_uint(0) # Formula Slot 0

# Formula Pins
builder.add_8bit_uint(30)
builder.add_8bit_uint(32)
builder.add_8bit_uint(34)
builder.add_8bit_uint(36)
builder.add_8bit_uint(38)
builder.add_8bit_uint(40)
builder.add_8bit_uint(42)
builder.add_8bit_uint(44)

# Trip Recovery time in seconds
builder.add_16bit_uint(300)

# Trip Formula cstring
builder.add_string("L1U > 253.0\0")

payload = builder.build()
formularegisters = builder.to_registers()

rq = client.write_registers(151,formularegisters,unit=UNIT)
print("formula registers sent")
print("error: {}".format(rq))
time.sleep(1)
rq = client.write_coil(1,True,unit=UNIT) # all data written, advertise update

while(True):

    time.sleep(5)
    rr = client.read_holding_registers(80, 66, unit=UNIT)
    #assert not rr.isError()  # test that calls was OK
    print("error: {}".format(rr))
    #assert rr.registers[0] == 10  # nosec test the expected value
    txt = f"### address 1 is: {str(rr.registers[0])}"
    log.debug(txt)

    finals = [0.0] * 33

    for i in range(0,66,2):
        bits = (rr.registers[i+1] << 16) + rr.registers[i]
        s = struct.pack('>L', bits)
        finals[int(i/2)] = struct.unpack('>f', s)[0]
        
    
    

    print("voltage:" + str(finals[0]))
    print("current:" + str(finals[3]))
    print("power:" + str(finals[6]))
    print("energy:" + str(finals[9]))
    print("frequency:" + str(finals[12]))
    print("pf:" + str(finals[15]))

    print("avg_voltage:" + str(finals[18]))
    print("avg_current:" + str(finals[21]))
    print("avg_power:" + str(finals[24]))
    print("avg_frequency:" + str(finals[27]))
    print("avg_pf:" + str(finals[30]))


    insert(time.time(), finals[0], finals[3], finals[6], finals[9], finals[12], finals[15])
