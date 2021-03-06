import serial
import sys
import datetime
import time
from gpiozero import LED, Button
import RPi.GPIO as GPIO
from time import sleep
import datetime
from firebase import firebase
import Adafruit_DHT

from urllib.request import urlopen
import json
import os
from functools import partial

ser = serial.Serial('/dev/ttyUSB0')   # print the serial data sent by UNO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Sensor should be set to Adafruit_DHT.DHT11,
# Adafruit_DHT.DHT22, or Adafruit_DHT.AM2302.
sensor = Adafruit_DHT.DHT22

# Example using a Beaglebone Black with DHT sensor
# connected to pin P8_11.
pin = 18

# Try to grab a sensor reading.  Use the read_retry method which will retry up
# to 15 times to get a sensor reading (waiting 2 seconds between each retry).
humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

firebase = firebase.FirebaseApplication('https://rasp-dht22-and-soil.firebaseio.com/', None)

#firebase.put("/dht", "/temp", "0.00")
#firebase.put("/dht", "/humidity", "0.00")

init = False
# Broadcom pin-numbering scheme


def get_last_watered():
    try:
        f = open("last_watered.txt", "r")
        return f.readline()
    except:
        return "NEVER!"

def get_status(pin = 8):
    GPIO.setup(pin, GPIO.IN)
    return GPIO.input(pin)

def init_output(pin):
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
    GPIO.output(pin, GPIO.HIGH)

def auto_water(delay = 5, pump_pin = 17, water_sensor_pin = 18):
    consecutive_water_count = 0
    init_output(pump_pin)
    print("Here we go! Press CTRL+C to exit")
    try:
        while 1 and consecutive_water_count < 10:
            time.sleep(delay)
            wet = get_status(pin = water_sensor_pin) == 0
            if not wet:
                if consecutive_water_count < 5:
                    pump_on(pump_pin, 1)
                consecutive_water_count += 1
            else:
                consecutive_water_count = 0
    except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
        GPIO.cleanup() # cleanup all GPI

def pump_on(pump_pin = 17, delay = 1):
    init_output(pump_pin)
    print("pump on!")
    f = open("last_watered.txt", "w")
    f.write("Last watered {}".format(datetime.datetime.now()))
    f.close()
    GPIO.output(pump_pin, GPIO.LOW)
    time.sleep(1)
    GPIO.output(pump_pin, GPIO.HIGH)

def update_firebase():

	ser.readline()  # read the serial data sent by the UNO
	humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
	if humidity is not None and temperature is not None:
		sleep(1)
		str_temp = ' {0:0.2f} *C '.format(temperature)
		str_hum  = ' {0:0.2f} %'.format(humidity)
		print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
		print (ser.readline())
	else:
		print('Failed to get reading. Try again!')
		sleep(5)

	data = {"temp": temperature, "humidity": humidity}
	firebase.post('/sensor/dht', data)

def soilMoist():
    msg = ser.readline(4)
    msg_decode = msg.decode('UTF-8')
    data = {"Soil-moisture" : msg_decode}
    firebase.post('/sersor/moisture', data)
    print(msg_decode)

while True:
	update_firebase()
	soilMoist()
	sleep(0.2)
