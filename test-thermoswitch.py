#!/usr/bin/python

import RPi.GPIO as GPIO
from time import sleep             # lets us have a delay

GPIO.setmode(GPIO.BCM) # GPIO Nummern statt Board Nummern

REL1 = 2 # Relais to power fan and 1000 W heat
REL2 = 3 # Relais to power fan and 2000 W heat
TST1 = 4 # Input to detect if we need to heat more

GPIO.setup(REL1, GPIO.OUT)   # setup GPIO for Relais 1
GPIO.setup(REL2, GPIO.OUT)   # setup GPIO for Relais 2
GPIO.setup(TST1, GPIO.IN, pull_up_down = GPIO.PUD_UP)    # setup GPIO for "ThermoStaT"

GPIO.output(REL1, GPIO.HIGH) # deactivate GPIO for Relais 1
GPIO.output(REL2, GPIO.HIGH) # deactivate GPIO for Relais 2




try:
  while True:
    print (GPIO.input(TST1))
    sleep(0.2)


except KeyboardInterrupt:      # trap a CTRL+C keyboard interrupt
  GPIO.output(REL1, GPIO.HIGH) # deactivate GPIO for Relais 1
  GPIO.output(REL2, GPIO.HIGH) # deactivate GPIO for Relais 2
  GPIO.cleanup()               # resets all GPIO ports used by this program
