#!/usr/bin/python

from sys import stderr
from pyfirmata import *
from time import sleep 
from datetime import datetime

LOW=0
HIGH=1

LEFT=0
RIGHT=1

motorCount = 2
motorSpeed = [0, 0]

# configure robot on bluetooth port and trigger a read thread
robot = Arduino("/dev/rfcomm0",baudrate=115200)
it=util.Iterator(robot)
it.start()

# identify the appropriate pins that motor controls are attached to
motorForwardPin = [robot.digital[pin] for pin in {2, 5}]
motorBackwardPin = [robot.digital[pin] for pin in {4, 7}]
motorSpeedPin = [robot.digital[pin] for pin in {3, 6}] # note these must be pwm pins

# identify the pins that analog sensors are attached to
reflectSensors = [robot.analog[pin] for pin in {2,3}]
lightSensors = [robot.analog[pin] for pin in {4,5}]

def setup():
  for motor in range(motorCount):
    # configure pins
    motorForwardPin[motor].mode = OUTPUT
    motorBackwardPin[motor].mode = OUTPUT
    motorSpeedPin[motor].mode = PWM
    # initialise values
    motorForwardPin[motor].write(LOW)
    motorBackwardPin[motor].write(LOW)
    motorSpeedPin[motor].write(0)
    
  for side in range(2):
    # configure pins
    reflectSensors[side].enable_reporting()
    lightSensors[side].enable_reporting()

#Set a speed between -1.0 and 1.0 for the given motor
def setSpeed(motor, speed):
    if speed > 0:
      motorBackwardPin[motor].write(LOW)
      motorForwardPin[motor].write(HIGH)
    elif speed < 0:
      motorForwardPin[motor].write(LOW)
      motorBackwardPin[motor].write(HIGH)
    else:
      motorForwardPin[motor].write(LOW)
      motorBackwardPin[motor].write(LOW)      
    motorSpeedPin[motor].write(abs(speed))
    motorSpeed[motor] = speed

def test():
  speed = 0
  pause = 0.010
  for value in range(256):
    speed = value/255.0
    setSpeed(RIGHT,speed)
    sleep(pause)
  for value in range(256):
    speed = (255-value)/255.0
    setSpeed(RIGHT,speed)
    sleep(pause)
  for value in range(256):
    speed = value/255.0
    setSpeed(LEFT,speed)
    sleep(pause)
  for value in range(256):
    speed = (255-value)/255.0
    setSpeed(LEFT,speed)
    sleep(pause)

# initialise the pins properly
setup()

# this runs only when run as a .py, not when imported
if __name__ == '__main__':
  try:
    print "Starting loop",
    print >> stderr, str(datetime.now())
    while True:
      test()
  finally:
    print "Loop ended",
    print >> stderr, str(datetime.now())
