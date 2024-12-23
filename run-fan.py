#!/usr/bin/env python

#########################
#
# run-fan turns a fan on and off when temperature exceeds temperature
# thresholds.
#
#########################

#########################
#
# run-fan requires an S8050 NPN transistor and a resistor to be connected
# as follows:
#   flat side of S8050 faces this way >
#   S8050 pin c: connects to black (-) wire on fan
#   S8050 pin b: connects to 110 Ohm Resistor and to GPIO pin 25
#   S8050 pin e: connects to ground GPIO pin
#   fan red (+): connects to 5v GPIO pin on raspberry pi 3
#
# GPIO pin 25 is used, but it can be changed
#
#########################

#########################
#
# run-fan starts automatically using systemd
#
# Create a systemd service file using:
#   $ sudo nano /lib/systemd/system/run-fan.service
#
# with the contents as shown below
# remove # and leading spaces:
#   [Unit]
#   Description=run fan when hot
#   After=meadiacenter.service
#
#   [Service]
#   # If User and Group are not specified as root, then it won't work
#   User=root
#   Group=root
#   Type=simple
#   ExecStart=/usr/bin/python /home/osmc/run-fan.py
#   Restart=Always
#
#   [Install]
#   WantedBy=multi-user.target
#
# end of the run-fan.service
# ctrl-o, ENTER, ctrl-x to save and exit the nano editor
#
# After any changes to /lib/systemd/system/run-fan.service:
#    sudo systemctl daemon-reload
#    sudo systemctl enable run-fan.service
#    sudo reboot
#
# Ensure the run-fan.service in systemd is enabled and running:
#    systemctl list-unit-files | grep enabled
#    systemctl | grep running | grep fan
#    systemctl status run-fan.service -l
#
# If there are any issues with starting the script using systemd, 
# then examine the journal using:
#    sudo journalctl -u run-fan.service
#
#########################

#########################
#
# The original script is from:
#    Author: Edoardo Paolo Scalafiotti <edoardo849@gmail.com>
#    Source: https://hackernoon.com/how-to-control-a-fan-to-cool-the-cpu-of-your-raspberrypi-3313b6e7f92c
#
#########################

#########################
import os
import time
import signal
import sys
import RPi.GPIO as GPIO
import datetime

#########################
# sleep timer
sleepTime = 30

# want to write unbuffered to file
logName = "/home/pi/run-fan/logs/run-fan-default.log"
fileLog = open(logName, 'w+', buffering=1)

#########################
# Log messages should be time stamped
def timeStamp():
    t = time.time()
    s = datetime.datetime.fromtimestamp(t).strftime('%Y/%m/%d %H:%M:%S - ')
    return s

def dateStamp():
    t = time.time()
    d = datetime.datetime.fromtimestamp(t).strftime('%Y.%m.%d')
    return d

# Write messages in a standard format
def printMsg(s):
    fileLog.write(timeStamp() + s + "\n")

#########################
class Pin(object):
    pin = 25        # GPIO or BCM pin number to turn fan on and off

    def __init__(self):
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.pin, GPIO.OUT)
            printMsg("Initialized: run-fan using GPIO pin: " + str(self.pin))
            func = GPIO.gpio_function(self.pin)
            printMsg("GPIO pin: " + str(self.pin) + " set to " + str(func))
        except:
            printMsg("If method setup doesn't work, need to run script as sudo")
            exit

    # resets all GPIO ports used by this program
    def exitPin(self):
        GPIO.cleanup()

    def set(self, state):
        GPIO.output(self.pin, state)

# Fan class
class Fan(object):
    fanOff = True

    def __init__(self):
        self.fanOff = True

    # Turn the fan on or off
    def setFan(self, temp, on, myPin):
        if on:
            printMsg("Turning fan on " + str(temp))
        else:
            printMsg("Turning fan off " + str(temp))
        myPin.set(on)
        self.fanOff = not on

# Temperature class
class Temperature(object):
    cpuTemperature = 0.0
    startTemperature = 0.0
    stopTemperature = 0.0

    def __init__(self):
        # Start temperature in Celsius
        #   Maximum operating temperature of Raspberry Pi 3 is 85C
        #   CPU performance is throttled at 82C
        #   running a CPU at lower temperatures will prolong its life
        self.startTemperature = 67.0

        # Wait until the temperature is M degrees under the Max before shutting off
        self.stopTemperature = self.startTemperature - 5.0

        printMsg("Start fan at: " + str(self.startTemperature))
        printMsg("Stop fan at: " + str(self.stopTemperature))

    def getTemperature(self):
        # need to specify path for vcgencmd
        # res = os.popen('/opt/vc/bin/vcgencmd measure_temp').readline()
        # self.cpuTemperature = float((res.replace("temp=","").replace("'C\n","")))
        res = os.popen('cat /sys/class/thermal/thermal_zone0/temp').readline()
        self.cpuTemperature = float(res)/1000

    # Using the CPU's temperature, turn the fan on or off
    def checkTemperature(self, myFan, myPin):
        self.getTemperature()
        if self.cpuTemperature > self.startTemperature:
            # need to turn fan on, but only if the fan is off
            if myFan.fanOff:
                myFan.setFan(self.cpuTemperature, True, myPin)
        elif self.cpuTemperature <= self.stopTemperature:
            # need to turn fan off, but only if the fan is on
            if not myFan.fanOff:
                myFan.setFan(self.cpuTemperature, False, myPin)

#########################
printMsg("Starting: run-fan")
try:
    myPin = Pin()
    myFan = Fan()
    myTemp = Temperature()
    while True:
        myTemp.checkTemperature(myFan, myPin)
        # check if log file should be closed
        tmp = "/home/pi/run-fan/logs/run-fan-{}.log".format(dateStamp())
        if tmp != logName:
            fileLog.close()
            logName = tmp
            fileLog = open(logName, 'w+', buffering=1)
            # delete old logs
            os.system("find /home/pi/run-fan/logs/ -mtime +14 -delete")
        # Read the temperature every N sec (sleepTime)
        # Turning a device on & off can wear it out
        time.sleep(sleepTime)

except KeyboardInterrupt: # trap a CTRL+C keyboard interrupt
    printMsg("keyboard exception occurred")
    myPin.exitPin()
    fileLog.close()

except:
    printMsg("ERROR: an unhandled exception occurred")
    myPin.exitPin()
    fileLog.close()

