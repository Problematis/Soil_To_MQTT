import utime
import ntptime
import network
import secrets
import Soil_Sensor_Config
import json
import statistics
from machine import ADC, Pin, I2C
from umqtt.simple import MQTTClient

from ota import OTAUpdater
#set up wifi connection
ssid = secrets.WiFi_SSID
password = secrets.Wifi_Password


firmware_url = "https://raw.githubusercontent.com/Problematis/Soil_To_MQTT/main/"
ota_updater = OTAUpdater(ssid, password, firmware_url, "main.py")
ota_updater.download_and_install_update_if_available()



mqtt_server = secrets.MQTT_IP_Address
client_id = Soil_Sensor_Config.mqtt_client_id
user_t = secrets.MQTT_User
password_t = secrets.MQTT_Password
topic_pub = Soil_Sensor_Config.mqtt_topic


led = Pin("LED", Pin.OUT)
led.value(1) # LED On
led.value(0) # LED Off

# set up averaging for soil readings
Index = 0
Value = 0
Window_Size = 20

soil_sensor_1_readings = [0 for i in range(Window_Size)]
soil_sensor_1_sum = 0
soil_sensor_1_median = 0

soil_sensor_2_readings = [0 for i in range(Window_Size)]
soil_sensor_2_sum = 0
soil_sensor_2_median = 0

soil_sensor_3_readings = [0 for i in range(Window_Size)]
soil_sensor_3_sum = 0
soil_sensor_3_median = 0

readDelay = 30 # delay between readings

soil_sensor_1 = ADC(Pin(26)) # Soil moisture PIN reference
soil_sensor_2 = ADC(Pin(27)) # Soil moisture PIN reference
soil_sensor_3 = ADC(Pin(28)) # Soil moisture PIN reference

soil_sensor_1_number = Soil_Sensor_Config.Soil_Sensor_1  # actual label on the soil sensor
soil_sensor_2_number = Soil_Sensor_Config.Soil_Sensor_2  # actual label on the soil sensor
soil_sensor_3_number = Soil_Sensor_Config.Soil_Sensor_3  # actual label on the soil sensor

soil_sensor_1_readings = []
soil_sensor_2_readings = []
soil_sensor_3_readings = []

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# Wait for connect or fail
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    utime.sleep(1)

# Handle connection error
if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    s = 3
    while s > 0:
        s -= 1
        led.value(1)
        utime.sleep(0.5)
        led.value(0)
        utime.sleep(0.5)
        
    #print('connected')
    status = wlan.ifconfig()
    print( 'Connected to ' + ssid + '. ' + 'Device IP: ' + status[0] )

def mqtt_connect():
    client = MQTTClient(client_id, mqtt_server, user=user_t, password=password_t, keepalive=0)
    client.connect()
    print('Connected to %s MQTT Broker'%(mqtt_server))
    return client

def reconnect():
    print('Failed to connect to the MQTT Broker. Reconnecting...')
    utime.sleep(5)
#    machine.reset()

def mqtt_publish():
    client.publish(topic_pub, JsonPayload)
    print('Message published to MQTT')   

def mqtt_disconnect():
    client.disconnect()        
    print('Disconnected from %s MQTT Broker'%(mqtt_server))

ntptime.settime()

rtc=machine.RTC()
    
while True:
    
# capture Sensor data     
    for i in range(Window_Size):
        reading = soil_sensor_1.read_u16()
        soil_sensor_1_readings.append(reading)
        print(soil_sensor_1_readings)
        
        reading = soil_sensor_2.read_u16()
        soil_sensor_2_readings.append(reading)
        print(soil_sensor_2_readings)
        
        reading = soil_sensor_3.read_u16()
        soil_sensor_3_readings.append(reading)
        print(soil_sensor_3_readings)        
        
        utime.sleep(readDelay)
           
    soil_sensor_1_median = statistics.median(soil_sensor_1_readings)
    print(soil_sensor_1_median)
    soil_sensor_1_readings = []
    
    soil_sensor_2_median = statistics.median(soil_sensor_2_readings)
    print(soil_sensor_2_median)
    soil_sensor_2_readings = []
    
    soil_sensor_3_median = statistics.median(soil_sensor_3_readings)
    print(soil_sensor_3_median)
    soil_sensor_3_readings = []    
      
    timestamp=rtc.datetime()
    timestring="%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] +
                                                timestamp[4:7])
 # construct JSON MQTT message
    JsonPayload = json.dumps({
        "Time": timestring,
        "Soil_Sensor_" +soil_sensor_1_number +"_Median": soil_sensor_1_median,
        "Soil_Sensor_" +soil_sensor_2_number +"_Median": soil_sensor_2_median,
        "Soil_Sensor_" +soil_sensor_3_number +"_Median": soil_sensor_3_median
    })
    print(JsonPayload)
 
    try:
        client = mqtt_connect()
    except:
        print('Failed to connect to the MQTT Broker.')
    
    try:
        mqtt_publish()
    except:
        print('Failed to publish to the MQTT Broker.')

