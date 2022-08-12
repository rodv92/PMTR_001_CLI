/*
Modbus RTU Client for PMTR-001 Server Device.
Features :
Request of instantaneous values for voltage, current, power, frequency, power factor.
Request of moving averaged values for voltage, current, power, frequency, power factor.
Request / reset of energy counter.
Actuation of Solid State Relay. on/off
Set Relay state after power loss (off/on/last state)
*/

#include <ArduinoRS485.h> // ArduinoModbus depends on the ArduinoRS485 library
#include <ArduinoModbus.h>
int read_total;
int read_fail;
double fail_pct;
int ret;
const int totalRegisters = 22;
int RegisterIndexLoop;


bool DeviceBitMap[256];
long AverageRequestDuration;
uint8_t TotalOnlineDevices;
uint16_t InterFrameTimeMillis = 5;

int VoltageModbusRegister[2] = {0};
int CurrentModbusRegister[2] = {0};
int PowerModbusRegister[2] = {0};
int EnergyModbusRegister[2] = {0};
int FrequencyModbusRegister[2] = {0};
int PowerFactorModbusRegister[2] = {0};

int AllModbusRegisters[totalRegisters];

void SaveData()
{
        
}

void ScanDevices(uint8_t devaddr_start, uint8_t devaddr_stop, bool *isDevOnline, long &AvgReqDur, uint8_t &total_online )
{
  
  uint8_t k;
  long timestart;
  long request_duration;
  long request_duration_avg;
  // scans modbus devices on the PLC bus.
  isDevOnline += devaddr_start;
  for(k=devaddr_start;k<devaddr_stop;k++)
  {
      timestart = micros()
      ret = ModbusRTUClient.requestFrom(k, HOLDING_REGISTERS, 80, totalRegisters);
      request_duration = micros() - timestart;
      if ((!ret) || (ret != totalRegisters)) 
      {
        Serial.println(ModbusRTUClient.lastError());
        *isDevOnline = false;
      }
      else
      {
        *isDevOnline = true;
        request_duration_avg += request_duration;
        total_online++;
      }
      
      isDevOnline++;
  }
  if (total_online > 0)
  {
      request_duration_avg /= total_online;
  }
  else
  {
    request_duration_avg = -1;
    avgReqDur = request_duration_avg;  
  }
  
}

void setup() {
  read_total = 0;
  read_fail = 0;
  fail_pct = 0.0;
  Serial.begin(9600);
  Serial1.begin(9600);
  
  while (!Serial);

  Serial.println("Modbus RTU Client Toggle");

  // start the Modbus RTU client
  if (!ModbusRTUClient.begin(9600)) {
    Serial.println("Failed to start Modbus RTU Client!");
    while (1);
  }

  ScanDevices(0,255,DeviceBitMap,AverageRequestDuration,TotalOnlineDevices)

  // let's compute fastest possible polling cycle. To be reported to GUI
  TotalCycleTimeSec = int((int(AverageRequestDuration/1000) + InterFrameTimeMillis)*TotalOnlineDevices/1000);
 
}

void ScanAllDevices()
{

  uint8_t k;
  uint16_t addr;
  flash.eraseSection(0,40960);
        

  for (k=0;k<256;k++)
  {

  for (RegisterIndexLoop = 0; RegisterIndexLoop < totalRegisters; RegisterIndexLoop++)
  {
    AllModbusRegisters[RegisterIndexLoop] = 0;
  }   


    if (DeviceBitMap[k])
    {

      ret = ModbusRTUClient.requestFrom(0x01, HOLDING_REGISTERS, 80, totalRegisters);

      if ((!ret) || (ret != totalRegisters)) 
      {
        Serial.print("failed! ");
        Serial.println(ModbusRTUClient.lastError());
        read_fail++;
      } 
      else 
      {
        Serial.println("success");
        read_total++;
        RegisterIndexLoop = 0;

        while (ModbusRTUClient.available()) 
        {
        
          addr = (k*totalRegisters + RegisterIndexLoop)*sizeof(uint16_t);
          AllModbusRegisters[RegisterIndexLoop] = int(ModbusRTUClient.read());
          flash.writeWord(addr,AllModbusRegisters[RegisterIndexLoop])
          RegisterIndexLoop++;
        }
   
}


      
    }
  }



}

void loop() {

for (RegisterIndexLoop = 0; RegisterIndexLoop < totalRegisters; RegisterIndexLoop++)
{
  AllModbusRegisters[RegisterIndexLoop] = 0;
}   

ret = ModbusRTUClient.requestFrom(0x01, HOLDING_REGISTERS, 80, totalRegisters);

if ((!ret) || (ret != totalRegisters)) 
{
  Serial.print("failed! ");
  Serial.println(ModbusRTUClient.lastError());
  read_fail++;
} 
else 
{
  Serial.println("success");
  read_total++;
  RegisterIndexLoop = 0;

  while (ModbusRTUClient.available()) 
  {
    AllModbusRegisters[RegisterIndexLoop] = int(ModbusRTUClient.read());
    RegisterIndexLoop++;
  }
   
}

float voltage = 0.0;
float current = 0.0;
float power = 0.0;
float energy = 0.0;
float frequency = 0.0;
float pf = 0.0;

float avg_voltage = 0.0;
float avg_current = 0.0;
float avg_power = 0.0;
float avg_energy = 0.0;
float avg_frequency = 0.0;
float avg_pf = 0.0;



memcpy(&voltage, AllModbusRegisters, sizeof(voltage));
memcpy(&current, &AllModbusRegisters[2], sizeof(current));
memcpy(&power, &AllModbusRegisters[4], sizeof(power));
memcpy(&energy, &AllModbusRegisters[6], sizeof(energy));
memcpy(&frequency, &AllModbusRegisters[8], sizeof(frequency));
memcpy(&pf, &AllModbusRegisters[10], sizeof(pf));

memcpy(&avg_voltage, &AllModbusRegisters[12], sizeof(avg_voltage));
memcpy(&avg_current, &AllModbusRegisters[14], sizeof(avg_current));
memcpy(&avg_power, &AllModbusRegisters[16], sizeof(avg_power));
memcpy(&avg_frequency, &AllModbusRegisters[18], sizeof(avg_frequency));
memcpy(&avg_pf, &AllModbusRegisters[20], sizeof(avg_pf));



  // wait for 1 second
  delay(5000);
  Serial.print("voltage: ");
  Serial.println(voltage,2);

  Serial.print("current: ");
  Serial.println(current,2);

  Serial.print("power: ");
  Serial.println(power,2);

  Serial.print("energy: ");
  Serial.println(energy,2);

  Serial.print("frequency: ");
  Serial.println(frequency,2);

  Serial.print("pf: ");
  Serial.println(pf,2);
  Serial.flush();

  fail_pct = 100.0 * float(read_fail)/float(read_total);  
  Serial.print("fail_pct: ");
  Serial.println(String(fail_pct));
  Serial.flush();
}
