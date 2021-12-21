#!/usr/bin/python
##########################################
#   Author: Daisuke Otagiri
#   Course: EECS 113
#   Final Project
#   Created: 4, June 2021
##########################################

#import Python modules
import Adafruit_DHT
import RPi.GPIO as GPIO
import threading
import time
import drivers
import math
from signal import pause
from datetime import datetime
import decimal
import cimis
from cimis import get_cimis_data_for
from cimis import cimis_data

HOUR = (60*60)

#Declare LCD pin
display = drivers.Lcd()

#Declare PIR pin
PIR_pin = 17

#Declare DHT pin
DHT_PIN = 4
DHT_SENSOR = Adafruit_DHT.DHT11

#Declare Button pins
BTN_G = 23  #Green button
BTN_B = 24  #Blue button
BTN_R = 25  #Red button

#Declare LED pins
GLED = 6    #GPIO 6
BLED = 13   #GPIO 13
RLED = 19   #GPIO 19

#Declare flags
ambient_flag = 0        #PIR
stop_threads = False    #to kill threads
door_flag = 0           #door
hvac_flag = 0           #HVAC
desired_temp = 72        #desired temperature [65-85]
weather_index = 0       #weather index
avg_temp = 0            #average temp
avg_humid = 0           #average humid       
hvac_display_flag = 0       #to display heater on and ac on

#global strings for displayLCD function
str_humid = ""

#mutex initialize
mutex = threading.Lock()

#variables for cimis
starting_hour = -1

def setupGPIO(): 
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup([BTN_G, BTN_B, BTN_R], GPIO.IN, pull_up_down=GPIO.PUD_UP) #3 buttons
    GPIO.setup(PIR_pin, GPIO.IN) #PIR 
    GPIO.setup([GLED, BLED, RLED], GPIO.OUT) # setup LED's


def checkTemp():
    global mutex

    temp_event.wait()
   
    global str_humid
    global weather_index
    global avg_temp
    global avg_humid
    global hvac_flag
    current_hour = starting_hour
    
    #read temperature from DHT11 and display it on LCD here
    #this function runs every second

    #three temperature variables to take average of
    temp1 = 0.0
    temp2 = 0.0
    temp3 = 0.0
    
    while temp_event.is_set():
        #acquire lock
        mutex.acquire()

        if door_flag == 0: 
            #####################   Temp 1   #######################
            humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
            if (temperature is not None):
                temp1 = temperature
            #else:
            #    print("Sensor failure. Check wiring.")
            time.sleep(0.3) #want to get 3 temperatures in 1 second to average

            #####################   Temp 2   #######################
            humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
            if (temperature is not None):
                temp2 = temperature 
            #else:
            #    print("Sensor failure. Check wiring.")
            time.sleep(0.3)

            #####################   Temp 3   #######################
            humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
            if (temperature is not None):
                temp3 = temperature
            #else:
            #    print("Sensor failure. Check wiring.")
            time.sleep(0.3)
           
            data = get_cimis_data_for(current_hour)
            while(data is None or data.get_humidity() is None):
                if data is None:
                    print("Failed to request data from CIMIS. Will try again in an hour")
                else: 
                    print("Failed to request data from CIMIS. Will try again in an hour")
                time.sleep(HOUR) #try again in an hour
                print("Attempting to get cimis data for hour " + str(current_hour) + ":00")
                data = get_cimis_data_for(current_hour)

            if data.get_humidity() is not None:
                avg_humid = float(data.get_humidity())

            avg_temp = round((temp1+temp2+temp3)/3)
            #avg_humid = round((humid1+humid2+humid3)/3)

            #str_humid = str(round(humid1 + humid2 + humid3) / 3)
            avg_temp = round(avg_temp * (9/5)) + 32
            weather_index = round(avg_temp + 0.05 * avg_humid)
            print("current hour is: " + str(current_hour) + ":00")
            print("temp: " + str(avg_temp))
            print("humidity: " + str(avg_humid))
            print("weather index: " + str(weather_index))
            displayLCD()
        else:
            time.sleep(0.9)
            displayLCD()

        #release lock
        mutex.release()
        time.sleep(0.1)
def checkDoor(channel): #control door with green button
    global door_flag
    global mutex
    
    if door_flag == 0: #when button is first pushhed then door is open
        door_flag = 1       #opened door so flag = 1
        
        mutex.acquire()
        display.lcd_clear()
        #display that the door is open
        display.lcd_display_string("DOOR/WINDOW OPEN", 1)
        display.lcd_display_string("  HVAC HALTED", 2)

        time.sleep(3)   #display for 3s
        mutex.release()
    elif door_flag == 1:  #door open
        door_flag = 0   #door closed so flag =0

        mutex.acquire()
        display.lcd_clear()
        display.lcd_display_string("  DOOR CLOSED", 1)
        display.lcd_display_string("   HVAC START", 2)

        time.sleep(3)   #display for 3s
        mutex.release()

def ambientLightControl(channel):
    global start_time
    global ambient_flag

    i = GPIO.input(PIR_pin)
    if i == 1:
        event.clear()
        GPIO.output(GLED,1) #turn green led on
        ambient_flag = 1    #ambient_flag up
    else:
        t1 = threading.Thread(target=timer, daemon=True) 
        t1.start() #start timer for 10s
        event.set()

def timer():
    #reset timer everytime PIR detects movement
    event.wait()
    global ambient_flag

    start_time = time.time()
    current_t = time.time()
    while time.time() - start_time < 10 and event.is_set():
        current_t = time.time() 
    if current_t - start_time > 10:
        ambient_flag = 0
        GPIO.output(GLED, 0) #turn green LED off after 10s of no movement

def displayLCD():
    global ambient_flag
    global hvac_flag
    global door_flag

    global desired_temp
    global str_tem
    global weather_index
       
    LIGHT = ""
    HVAC = ""
    DOOR = ""

    #PIR Sensor
    if ambient_flag == 0:
        LIGHT = "OFF"
    else:
        LIGHT = "ON"

    #HVAC
    if hvac_flag == 0:
        HVAC = "OFF"
    elif hvac_flag == 1:
        HVAC = "AC"
    else:            
        HVAC = "HEAT"

    #Door
    if door_flag == 0:
        DOOR = "SAFE"
    else:
        DOOR = "OPEN"
    
    str_temp = str(avg_temp)
    str_dtemp = str(desired_temp)
    str_weather_index = str(weather_index)
    #display 
    display.lcd_clear()
    display.lcd_display_string(str_weather_index + "/" + str_dtemp + "     D:" + DOOR, 1)
    display.lcd_display_string("H:" + HVAC + "     L:" + LIGHT, 2)

def heater(channel):
    global avg_temp
    global weather_index
    global desired_temp
    global hvac_flag
    global door_flag
    
    #hvac_flag = {  0    off
    #               1   AC
    #               2   Heat
    n_state = hvac_flag
 
    if door_flag ==0:
        if desired_temp < 85: #range of [65-85]
            desired_temp += 1 
        if weather_index >= desired_temp + 3: #if weather is 3 degrees above desired temp
            GPIO.output(BLED, 1)
            hvac_flag = 1   #set AC on

            if n_state != hvac_flag:
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("HVAC AC ON", 1)
                time.sleep(3)
                mutex.release()

        elif weather_index <= desired_temp - 3: #if weather is 3 degrees below desired temp
            GPIO.output(RLED, 1)
            hvac_flag = 2 #set heater on

            if n_state != hvac_flag:
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("HVAC HEATER ON", 1)
                time.sleep(3)
                mutex.release()
        else:
            GPIO.output(RLED, 0)
            GPIO.output(BLED, 0)
            hvac_flag = 0
            if n_state == 1: #if ac is on, then turn it off
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("HVAC AC OFF", 1)
                time.sleep(3) #display for 3 seconds
                mutex.release()
            elif n_state == 2: #if heater is on, turn it off
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("HVAC HEATER OFF", 1)
                time.sleep(3)
                mutex.release()
        


def AC(channel):
    global door_flag
    global avg_temp
    global weather_index
    global desired_temp
    global hvac_flag

    n_state = hvac_flag

    if door_flag ==0:
        #change lower bound to 60 for video demo
        #if desired_temp > 60:
        if desired_temp > 65: #make sure it stays in range  
            desired_temp -=1
        if weather_index >= desired_temp + 3: #if weather is 3 degrees above desired temp
            GPIO.output(BLED, 1)
            hvac_flag = 1   #set AC on

            if n_state != hvac_flag:
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("HVAC AC ON", 1)
                time.sleep(3)
                mutex.release()

        elif weather_index <= desired_temp - 3: #if weather is 3 degrees below desired temp
            GPIO.output(RLED, 1)
            hvac_flag = 2 #set heater on

            if n_state != hvac_flag:
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("HVAC HEATER ON", 1)
                time.sleep(3)
                mutex.release()
        else:
            GPIO.output(RLED, 0)
            GPIO.output(BLED, 0)
            hvac_flag = 0
            if n_state == 1: #if ac is on, then turn it off
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("HVAC AC OFF", 1)
                time.sleep(3) #display for 3 seconds
                mutex.release()
            elif n_state == 2: #if heater is on, turn it off
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("HVAC HEATER OFF", 1)
                time.sleep(3)
                mutex.release()
        
        
def cleanup():
    display.lcd_clear()
    GPIO.output([GLED, BLED, RLED], GPIO.LOW) #turn LED's off
    GPIO.cleanup()


# Main body of code
if __name__ == "__main__":
    try:
        setupGPIO()
        
        #Event handlers for buttons
        GPIO.add_event_detect(PIR_pin, GPIO.BOTH, ambientLightControl, bouncetime = 150) #event for PIR sensor
        GPIO.add_event_detect(BTN_G, GPIO.RISING, checkDoor, bouncetime = 150) #green button --> door
        GPIO.add_event_detect(BTN_B, GPIO.RISING, AC, bouncetime = 150) #blue button --> decrease temp
        GPIO.add_event_detect(BTN_R, GPIO.RISING, heater, bouncetime = 150) #red button --> increase temp
        
        event = threading.Event()
        temp_event = threading.Event()
        print("Start threading")
        #collect cimis data from 2 hours ago
        starting_hour = time.localtime(time.time()).tm_hour - 2
       
        temp_thread = threading.Thread(target = checkTemp)
        temp_thread.daemon = True
        temp_thread.start()
        temp_event.set()

        print("Threading complete")
        print("Reading data from CIMIS...")

        while True:
            time.sleep(1e6)
    except KeyboardInterrupt:
        # If there is a KeyboardInterrupt (when you press ctrl+c), exit the program and cleanup
        print("Cleaning up!")
        display.lcd_clear()
        GPIO.output([GLED, BLED, RLED], GPIO.LOW) #turn LED's off
    
    finally:
        cleanup()

