#!/usr/bin/python

# EECS 113 - Assignment 4
# Created by: Daisuke Otagiri
# Date: 05/18/21

### import python Modules ###
import threading
import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False) #disable warnings
GPIO.setmode(GPIO.BCM)

#define pins for buttons
BTN_G = 25 #green button
BTN_R = 18 #red button
BTN_Y = 27 #yellow button
BTN_B = 22 #blue button

#define LED pins
GLED = 5   #green led
RLED = 6   #red led
YLED = 12  #yellow led
BLED = 13  #blue led

#setup I/O
GPIO.setup(BTN_G,GPIO.IN, pull_up_down=GPIO.PUD_UP) #green button
GPIO.setup(BTN_R,GPIO.IN, pull_up_down=GPIO.PUD_UP) #red button
GPIO.setup(BTN_Y,GPIO.IN, pull_up_down=GPIO.PUD_UP) #yellow button
GPIO.setup(BTN_B,GPIO.IN, pull_up_down=GPIO.PUD_UP) #blue button

GPIO.setup(GLED,GPIO.OUT, initial=GPIO.LOW) #green led
GPIO.setup(RLED,GPIO.OUT, initial=GPIO.LOW) #red led
GPIO.setup(YLED,GPIO.OUT, initial=GPIO.LOW) #yellow led
GPIO.setup(BLED,GPIO.OUT, initial=GPIO.LOW) #blue led

BTN2LED = {
    BTN_G: GLED,
    BTN_R: RLED,
    BTN_Y: YLED,
    BTN_B: BLED,
}

switch = 0
GPIO.output([GLED,RLED,YLED,BLED], False)
#this function takes care of blinking and is called by the blinking thread
def blink_thread():
    event.wait()
    count = 0.5
    started = time.time()
    while event.is_set():
        if GPIO.input(BTN_R): #if red button was pushed
            count -= 0.2    #slow down
        if GPIO.input(BTN_G): #if green button was pushed
            count += 0.2    #speed up
        if count < 0:
            count = 0
        if time.time() - started > 10: # advanced timer to stop at 10s
            break #stop blinking func

        GPIO.output([GLED, RLED, YLED, BLED], GPIO.HIGH)
        time.sleep(count) 
        GPIO.output([GLED, RLED, YLED, BLED], GPIO.LOW)
        time.sleep(count)

def handle(switch):
    t = None
   # when yellow and blue pressed simultaneously, enter blink mode
    if (GPIO.input(BTN_B) == False and GPIO.input(BTN_Y) == False):
        if switch == 0:
            event.set()
            switch = 1
            print("Starting thread")
            t = threading.Thread(target=blink_thread) 
            t.daemon = True
            t.start()   # start threading
        else:
            event.clear()
            print("turn off")
            switch = 0
            GPIO.output([GLED, RLED, YLED, BLED], False)
    return switch
event = threading.Event()
event.clear()
while True:
    switch = handle(switch)
    time.sleep(0.1)
