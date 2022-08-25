
from mqtt import MQTTClient
from network import WLAN
from network import LoRa
import machine
import time
import ubinascii
import pycom
from machine import Pin
from pysense import Pysense

from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
from MPL3115A2 import MPL3115A2,ALTITUDE,PRESSURE

py = Pysense()

lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868, bandwidth=LoRa.BW_250KHZ)
app_eui = ubinascii.unhexlify('')
app_key = ubinascii.unhexlify('')
#70b3d54990a17f82
lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)

# wait until the module has joined the network
while not lora.has_joined():
    time.sleep(2.5)
    print('Not yet joined...')

print('Joined')

# create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
# set the LoRaWAN data rate
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 4)
# make the socket blocking
# (waits for the data to be sent and for the 2 receive windows to expire)
s.setblocking(True)
#s.set_callback(loraWAN_cb)
str_send = bytearray([0x03, 0x67, 0x00, 0x00, 0x04, 0x02, 0x00, 0x00])

#def loraWAN_cb()

def sub_cb(topic, msg):
    print(msg)
    if msg == b'05_RED':
        pycom.rgbled(0xFF0000) # RED
    if msg == b'05_GREEN':
        pycom.rgbled(0x00FF00) # GREEN
    if msg == b'05_BLUE':
        pycom.rgbled(0x0000FF) # GREEN
    if msg == b'05_OFF':
        pycom.rgbled(0x000000) # GREEN
    if msg == b'05_LI':
        li = LIS2HH12(py)
        print("Acceleration: " + str(li.acceleration()))
        print("Roll: " + str(li.roll()))
        print("Pitch: " + str(li.pitch()))
        print("------------------------------")
    if msg == b'05_LT':
        print("------------------------------")
        lt = LTR329ALS01(py)
        print("Light (channel Blue lux, channel Red lux): " + str(lt.light()))
        print("------------------------------")
    if msg == b'05_MP':
        mp = MPL3115A2(py,mode=ALTITUDE) # Returns height in meters. Mode may also be set to PRESSURE, returning a value in Pascals
        print("MPL3115A2 temperature: " + str(mp.temperature()))
        print("Altitude: " + str(mp.altitude()))
        mpp = MPL3115A2(py,mode=PRESSURE) # Returns pressure in Pa. Mode may also be set to ALTITUDE, returning a value in meters
        print("Pressure: " + str(mpp.pressure()))
    if msg == b'05_SI':
        print("------------------------------")
        si = SI7006A20(py)
        print("Temperature: " + str(si.temperature())+ " deg C and Relative Humidity: " + str(si.humidity()) + " %RH")
        print("Dew point: "+ str(si.dew_point()) + " deg C")
        t_ambient = 24.4
        print("Humidity Ambient for " + str(t_ambient) + " deg C is " + str(si.humid_ambient(t_ambient)) + "%RH")


wlan = WLAN(mode=WLAN.STA)
#wlan.connect("labs", auth=(WLAN.WPA2, ''))
wlan.connect("Vodafone-23195D-2.4", auth=(WLAN.WPA2, ''))

while not wlan.isconnected():
    machine.idle()
print("Connected to WiFi\n")

dev_id = ""
user_id = ""
password_s =""
broker =  "mqtt.mydevices.com"
topic_s = ""

client = MQTTClient(dev_id, broker, user=user_id, password=password_s, port=1883)
print('Done')
client.set_callback(sub_cb)
print('Done')
client.connect()
print('Done')
client.subscribe(topic=topic_s)
print('Done')

pycom.heartbeat(False)
button = Pin('P14', mode = Pin.IN)

while True:
    if (button() == 0):
        #MQTT
        print(button)
        print("Sending ON")
        client.publish(topic=topic_s, msg="temp,t=2.40")

        #LORAWAN
        temp = int(si.temperature()*10)
        print("Temp: ", temp, " C")
        temp_bytes = temp.to_bytes(2,'big')
        str_send[2] = temp_bytes[0]
        str_send[3] = temp_bytes[1]
        v_bat = int(py.read_battery_voltage() * 100)
        print("V Battery: ", v_bat, " V")
        temp_v_bat = v_bat.to_bytes(2,'big')
        str_send[6] = temp_v_bat[0]
        str_send[7] = temp_v_bat[1]
        s.send(str_send)

    #MQTT receive data
    client.check_msg()
    #LORAWAN receive data
    data = s.recv(64)
    print(data)

    time.sleep(0.5)
