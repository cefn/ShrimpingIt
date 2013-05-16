#!/usr/bin/python

from __future__ import division
from sys import stderr
from pyfirmata import *
from time import sleep 
from itertools import chain
from datetime import datetime
from numpy import array

LOW=0
HIGH=1

LEFT=0
RIGHT=1

STEPTIME=0.1

motorSpeed = [0, 0]

maxSamples = 32

# configure robot on bluetooth port
robot = Arduino("/dev/rfcomm0",baudrate=115200)
it=util.Iterator(robot)

# identifies the LED pin for simplicity
led = robot.digital[13]

# lists the appropriate pins that motor controls are attached to
motorForwardPin = [robot.digital[pin] for pin in (7, 4)]
motorBackwardPin = [robot.digital[pin] for pin in (5, 2)]
motorSpeedPin = [robot.digital[pin] for pin in (6, 3)] # note these must be pwm pins

# lists the pins that analog sensors are attached to
reflectSensors = [robot.analog[pin] for pin in (3,2)]
lightSensors = [robot.analog[pin] for pin in (5,4)]

def resetSamples():
  global samplesRemembered, latestSample, sampleMean, sampleDeviation
  samplesRemembered = [] # empty list
  latestSample = None
  sampleMean = None
  sampleDeviation = None

def updateSamples(sensors):  
  global samplesRemembered, latestSample, sampleMean, sampleDeviation
  latestSample = sense(sensors) # get a reading from the sensors
  samplesRemembered.insert(0,latestSample) # store at beginning of list (in position zero) 
  if(len(samplesRemembered) > maxRemembered): # if a reading is old
    forgottenSample = samplesRemembered.pop() # remove from end
  leftArray = array([sample[LEFT] for sample in samplesRemembered])
  rightArray = array([sample[RIGHT] for sample in samplesRemembered])
  sampleMean=(leftArray.mean(),rightArray.mean())
  sampleDeviation=(leftArray.std(),rightArray.std())
  
def sense(sensors):
  return sensors[LEFT].read(), sensors[RIGHT].read()

def setup():
  
  for motor in (LEFT,RIGHT):
    # configure pins for digital/analog output
    motorForwardPin[motor].mode = OUTPUT
    motorBackwardPin[motor].mode = OUTPUT
    motorSpeedPin[motor].mode = PWM
    # initialise starting output values
    motorForwardPin[motor].write(LOW)
    motorBackwardPin[motor].write(LOW)
    motorSpeedPin[motor].write(0)
  
  # start an iterator thread to read analog values sent over serial
  if not(it.isAlive()):
    it.start()
    
  for side in (LEFT,RIGHT):
    # configure the pins to send over serial
    reflectSensors[side].enable_reporting()
    lightSensors[side].enable_reporting()
    
  # reset sampling of sensors
  resetSamples()
  
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

def goForward():
  setSpeed(LEFT, 1.0)
  setSpeed(RIGHT,1.0)
  sleep(STEPTIME)
  setSpeed(LEFT, 0)
  setSpeed(RIGHT,0)

def goBackward():
  setSpeed(LEFT, -1.0)
  setSpeed(RIGHT,-1.0)
  sleep(STEPTIME)
  setSpeed(LEFT, 0)
  setSpeed(RIGHT,0)

def turnLeft():
  setSpeed(LEFT, -1.0)
  setSpeed(RIGHT,1.0)
  sleep(STEPTIME)
  setSpeed(LEFT, 0)
  setSpeed(RIGHT,0)

def turnRight():
  setSpeed(LEFT, 1.0)
  setSpeed(RIGHT,-1.0)
  sleep(STEPTIME)
  setSpeed(LEFT, 0)
  setSpeed(RIGHT,0)

def bearLeft():
  setSpeed(LEFT, 0)
  setSpeed(RIGHT,1.0)
  sleep(STEPTIME)
  setSpeed(RIGHT, 0)

def bearRight():
  setSpeed(RIGHT, 0)
  setSpeed(LEFT,1.0)
  sleep(STEPTIME)
  setSpeed(LEFT, 0)
    
def test():
  speed = 0
  pause = 0.010
  for value in chain(range(256), reversed(range(256))):
    speed = value/255.0
    setSpeed(LEFT,speed)
    setSpeed(RIGHT,-speed)
    sleep(pause)
  for value in chain(range(256), reversed(range(256))):
    speed = value/255.0
    setSpeed(LEFT,-speed)
    setSpeed(RIGHT,speed)
    sleep(pause)
    
def navigateLine():
    values = sense(reflectSensors)
    difference = values[LEFT] - values[RIGHT]
    if abs(difference) < 0.1: # no turn needed        
      goForward()
    else: # difference is enough to warrant a turn
      if difference < 0 : # right value is higher, so left is over the tape
        turnLeft()
      else: # left value is higher, so right is over the tape
        turnRight()

def followLight():
    values = sense(lightSensors)
    inverted = [(1.0 - value) for value in values]
    mean = array(inverted).mean()
    difference = values[LEFT] - values[RIGHT]
    if difference < 0 : # right value is higher so turn to right
      bearRight()
    else: # left value is higher so turn to left
      bearLeft()

def stop():
  setSpeed(LEFT,0)
  setSpeed(RIGHT,0)
      
def end():
  if it.isAlive():
    it._Thread__stop()
  exit()

# this runs only when run as a .py, not when imported
if __name__ == '__main__':
  sleep(20)
  # initialise the pins properly
  setup()
  try:
    print "Starting loop",
    print >> stderr, str(datetime.now())
    while True:
      navigateLine()
        
  finally:
    print "Loop ended",
    print >> stderr, str(datetime.now())
