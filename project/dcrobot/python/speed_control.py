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

motorSpeed = [0, 0]

maxSamples = 32

# configure robot on bluetooth port
robot = Arduino("/dev/rfcomm0",baudrate=115200)

# identifies the LED pin for simplicity
led = robot.digital[13]

# lists the appropriate pins that motor controls are attached to
motorForwardPin = [robot.digital[pin] for pin in {4, 7}]
motorBackwardPin = [robot.digital[pin] for pin in {2, 5}]
motorSpeedPin = [robot.digital[pin] for pin in {3, 6}] # note these must be pwm pins

# lists the pins that analog sensors are attached to
reflectSensors = [robot.analog[pin] for pin in {2,3}]
lightSensors = [robot.analog[pin] for pin in {4,5}]

def resetSamples():
  global samplesRemembered, latestSample, sampleMean, sampleDeviation
  samplesRemembered = [] # empty list
  latestSample = None
  sampleMean = None
  sampleDeviation = None

def updateSamples(sensorLeft,sensorRight):
  global samplesRemembered, latestSample, sampleMean, sampleDeviation
  latestSample = (sensorLeft.read(),sensorRight.read()) # get a reading from the sensors
  samplesRemembered.insert(0,latestSample) # store at beginning of list (in position zero) 
  if(len(samplesRemembered) > maxRemembered): # if a reading is old
    forgottenSample = samplesRemembered.pop() # remove from end
  leftArray = array([sample[LEFT] for sample in samplesRemembered])
  rightArray = array([sample[RIGHT] for sample in samplesRemembered])
  sampleMean=(leftArray.mean(),rightArray.mean())
  sampleDeviation=(leftArray.std(),rightArray.std())

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
  
  # start an iterator thread to read analog valules sent over serial
  it=util.Iterator(robot)
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

# this runs only when run as a .py, not when imported
if __name__ == '__main__':
  sleep(20)
  # initialise the pins properly
  setup()
  try:
    print "Starting loop",
    print >> stderr, str(datetime.now())
    while True:
      updateSamples(reflectSensors[LEFT],reflectSensors[RIGHT])
      jointCurrentValue = latestSample[LEFT] + latestSample[RIGHT]
      jointHistoricalValue = sampleMean[LEFT] + sampleMean[RIGHT]
      if jointCurrentValue > jointHistoricalValue: # higher than average - speed up on side with highest sensor value
        if latestSample[LEFT] > latestSample[RIGHT]:
          speedup(LEFT)
        else:
          speedup(RIGHT)
      else: # lower than average - slow down on side with lowest sensor value
        if latestSample[LEFT] > latestSample[RIGHT]:
          slowdown(RIGHT)
        else:
          slowdown(LEFT)
        
  finally:
    print "Loop ended",
    print >> stderr, str(datetime.now())
