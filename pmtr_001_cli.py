import pymodbus
import pymysql
import argparse
import os
import logging
import time
import struct
import math
import numpy as np

from collections import deque
from os import remove
from os.path import splitext
from scipy.interpolate import PchipInterpolator
import fcntl

#--------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from pymodbus.client import ModbusSerialClient as ModbusClient
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

import signal
import sys

lock_filename = None

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    remove(lock_filename)
    sys.exit(0)


def insert(epoch,L1_voltage_V,L1_current_A,L1_active_power_W,L1_energy_kWh,L1_frequency_Hz,L1_pf,L2_voltage_V,L2_current_A,L2_active_power_W,L2_energy_kWh,L2_frequency_Hz,L2_pf,L3_voltage_V,L3_current_A,L3_active_power_W,L3_energy_kWh,L3_frequency_Hz,L3_pf):
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
              L2_voltage_V,
              L3_voltage_V,
              L1_current_A,
              L2_current_A,
              L3_current_A,
              L1_active_power_W,
              L2_active_power_W,
              L3_active_power_W,
              L1_energy_kWh,
              L2_energy_kWh,
              L3_energy_kWh,
              L1_frequency_Hz,
              L2_frequency_Hz,
              L3_frequency_Hz,
              L1_pf,
              L2_pf,
              L3_pf]
    

    cur.execute("INSERT INTO instant VALUES(NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", params) 
    print(f"{cur.rowcount} details inserted")
    conn.commit()
    conn.close()

def wait_int_sec():

    while(True):
        start = int(time.time())
        time.sleep(0.001)
        end = int(time.time())
        if(start != end):
            #integer second boundary plus/minus 0.001/2
            break

def start_client():

    client = ModbusClient(port="/dev/ttyS0",baudrate=9600,bytesize=8,parity="N",stopbits=1, timeout=5, retries=3)  # serial port

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

    UNIT = 0x7F
    BROADCAST = 0x0
    logging.basicConfig()


    logging.basicConfig(
        filename='/home/rod/scripts/pmtr_001_cli.log',  # Specify the log file name
        level=logging.INFO,      # Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format='%(asctime)s - %(levelname)s - %(message)s',  # Define the log message format
        filemode='a',            # 'a' for append, 'w' to overwrite the file on each run
        force=True
        )

    log = logging.getLogger()
    log.setLevel(logging.INFO)

    rq = client.write_coil(0,True,slave=BROADCAST)
    log.info("signalling units to go into time sync mode")
    #print("error: {}".format(rq))


    builder = BinaryPayloadBuilder(byteorder=Endian.BIG,wordorder=Endian.LITTLE)
    timeseconds = math.floor(time.time())
    timemilliseconds = math.floor(1000*(timeseconds % 1))
    builder.add_64bit_uint(timeseconds)
    builder.add_16bit_uint(timemilliseconds)
    payload = builder.build()
    epochregisters = builder.to_registers()

    rq = client.write_registers(146,epochregisters,slave=BROADCAST)
    log.info("epoch registers sent")
    #print("error: {}".format(rq))
    time.sleep(1)
    rq = client.write_coil(0,False,slave=BROADCAST)
    log.info("signalling to all units that time information has been written to registers")

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
    rq = client.write_coils(2,[False,False,True],slave=UNIT) # writing formula coils

    log.info("error: {}".format(rq))
    time.sleep(1)

    builder = BinaryPayloadBuilder(byteorder=Endian.BIG,wordorder=Endian.LITTLE)
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

    rq = client.write_registers(151,formularegisters,slave=UNIT)
    log.info("formula registers sent")
    #print("error: {}".format(rq))
    time.sleep(1)
    rq = client.write_coil(1,True,slave=UNIT) # all data written, advertise update

    run_id = 0
    error_count = 0
    error_rate_pct = 0
    interval = 0

    dq_instant = []
    i = 0
    while(i < 21):
        dq_instant.append(deque(maxlen=10))
        i += 1

    wait_int_sec()

    while(True):

        run_id += 1
        log.info("##########RUN:\t" + str(run_id))
        delay = max(2 - interval,0)
        if (delay != 0):
            time.sleep(delay) #ensure isochronous sampling
        else:
            wait_int_sec()

        start = time.time()
        rr = client.read_holding_registers(78, 35, slave=UNIT)
        interval = time.time() - start
        if(rr.isError()):
            log.info("RECV ERROR:{}".format(rr))
            log.info("TIMEOUT after:{}s".format(interval))
            error_count += 1
            error_rate_pct = 100*error_count/run_id
            log.info("ERROR RATE %: " +str( error_rate_pct) + "\n")
            continue
        else:
            log.info("RECV OK\n")
            log.info("time taken:{}s".format(interval))
            error_rate_pct = 100*error_count/run_id
            log.info("ERROR RATE %: " +str( error_rate_pct) + "\n")


        #assert not rr.isError()  # test that calls was OK
        #print("error: {}".format(rr))
        #assert rr.registers[0] == 10  # nosec test the expected value
        finals = [0] * 35

        for i in range(0,35):
            finals[i] = rr.registers[i]
            
            txt = "\n### address i,i+1 is:\t" + str(i) +"\t" + str(rr.registers[i])
            log.debug(txt)
        
        for j in range(0,20):

            txt = "\n### finals NOW values j is:\t" + str(j) +"\t" + str(finals[j])
            log.debug(txt)

        for j in range(20,35):
        
            txt = "\n### finals AVG values j is:\t" + str(j) +"\t" + str(finals[j])
            log.debug(txt)

        for k in range(0,3):
            log.debug("\n")
            log.debug("voltage:" + str(finals[2+k]))
            log.debug("current:" + str(finals[5+k]))
            log.debug("power:" + str(finals[8+k]))
            log.debug("energy:" + str(finals[11+k]))
            log.debug("frequency:" + str(finals[14+k]))
            log.debug("pf:" + str(finals[17+k]))
            log.debug("\n")
            log.debug("avg_voltage:" + str(finals[20+k]))
            log.debug("avg_current:" + str(finals[23+k]))
            log.debug("avg_power:" + str(finals[26+k]))
            log.debug("avg_frequency:" + str(finals[29+k]))
            log.debug("avg_pf:" + str(finals[32+k]))
            log.debug("\n")

            dq_instant[2+k].append(finals[2+k]/10.0)
            dq_instant[5+k].append(finals[5+k]/100.0)
            dq_instant[8+k].append(finals[8+k])
            dq_instant[11+k].append(finals[11+k]/10.0)
            dq_instant[14+k].append(finals[14+k]/10.0)
            dq_instant[17+k].append(finals[17+k]/100.0)
            

        dq_instant[20].append(start + interval/2)
        dq_instant[0].append(finals[0])
        dq_instant[1].append(finals[1])
        log.info("append to deque ok")

        i = 0
        instant_ndarrays_y = []
        timestamps_x = np.array(dq_instant[20])
        while(i < 20):
            instant_ndarrays_y.append(np.array(dq_instant[i]))
            instant_stack_y = np.stack(instant_ndarrays_y, axis=1)
            i += 1

        if(len(dq_instant[0]) == 10):
            print(instant_stack_y.shape)
            instant_interp = PchipInterpolator(timestamps_x, instant_stack_y,extrapolate=False)
            start_second = math.floor(timestamps_x[0] +1.0)
            stop_second = int(timestamps_x[-1] -1.0)
            evals = instant_interp(np.linspace(start_second, stop_second, num=stop_second-start_second+1, endpoint=True))
            print(evals)

        log.debug("5VDCBusVoltage:" + str(finals[0]))
        log.debug("12VDCBusVoltage:" + str(finals[1]))
        log.debug("\n")

        log.info("inserting into DB.\n")

        insert(time.time(), (finals[2]/10.0), (finals[5]/100.0), finals[8], (finals[11]/10), (finals[14]/10.0), (finals[17]/100.0),
            (finals[3]/10.0), (finals[6]/100.0), finals[9], (finals[12]/10), (finals[15]/10.0), (finals[18]/100.0),
            (finals[4]/10.0), (finals[7]/100.0), finals[10], (finals[13]/10), (finals[16]/10.0), (finals[19]/100.0))
    

def main():

    global lock_filename 
    lock_filename = '{}.lock'.format(splitext(__file__)[0])
    signal.signal(signal.SIGINT, signal_handler)
    
    with open(lock_filename, 'w') as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            print("Another instance of this script is already running.")
            return
        else:
            print('Lock acquired')
            start_client()

    
if __name__ == '__main__':
    main()
