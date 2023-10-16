#!/usr/bin/python

import RPi.GPIO as GPIO
from time import sleep             # lets us have a delay
import logging
from systemd.journal import JournaldLogHandler


logger = logging.getLogger(__name__)
journald_handler = JournaldLogHandler()
journald_handler.setFormatter(logging.Formatter(
    '[%(levelname)s] %(message)s'
))
logger.addHandler(journald_handler)
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)

# power levels
L1000 = 900  # power of 1000 W mode
L2000 = 1800 # power of 2000 W mode
LT = 1600    # trigger to detect "PHASE"

# GPIOs
REL1 = 2 # Relais to power fan and 1000 W heat
REL2 = 3 # Relais to power fan and 2000 W heat
TST1 = 4 # Input to detect if we need to heat more

# cycle time
DATA_CYCLE = 2 # seconds

# power variables
## data array
#             LG L1 L2 L3
power      = [ 0, 0, 0, 0 ]
power_old  = power[:]
power_diff = power[:]

## array strcture
#LC = int(); # connected "PHASE"
LC = 0; # default to LG
LG = 0;
L1 = 1;
L2 = 2;
L3 = 3;

# shm files
LG_FILE = '/mnt/s0hm/power'
L1_FILE = '/mnt/s0hm/power_L1'
L2_FILE = '/mnt/s0hm/power_L2'
L3_FILE = '/mnt/s0hm/power_L3'

GPIO.setwarnings(False)      # disable warning of already configured GPIOs
GPIO.setmode(GPIO.BCM)       # GPIO Nummern statt Board Nummern
GPIO.setup(REL1, GPIO.OUT)   # setup GPIO for Relais 1
GPIO.setup(REL2, GPIO.OUT)   # setup GPIO for Relais 2
GPIO.setup(TST1, GPIO.IN, pull_up_down = GPIO.PUD_UP) # setup GPIO for "ThermoStaT"

# read power into array from network shm file
def read_power(arr):
  try:
    arr[LG] = int(open(LG_FILE, 'r').read())
    arr[L1] = int(open(L1_FILE, 'r').read())
    arr[L2] = int(open(L2_FILE, 'r').read())
    arr[L3] = int(open(L3_FILE, 'r').read())
    return True
  except ValueError:
    return False

def calc_diff_power(diff, curr, old):
  diff[LG] = curr[LG] - old[LG]
  diff[L1] = curr[L1] - old[L1]
  diff[L2] = curr[L2] - old[L2]
  diff[L3] = curr[L3] - old[L3]
  return True

# check if all powers of absolute values of L1,L2,L3 is under the limit
def check_L1_L2_L3(arr, limit):
  for i in range(L1, L3+1): # from L1 to L3
    if abs(arr[i]) > limit:
      return False
  return True

def detect_static_power_consumption(cycles, limit):
  k = int(0)
  # conditions
  STATIC = False

  while not STATIC:
    # create copy of data set
    power_old = power[:]

    # check if data are valid
    if read_power(power) != True:
      STATIC = False
      continue

    # check if diff
    calc_diff_power(power_diff, power, power_old)
    print(power_diff)
    if check_L1_L2_L3(power_diff, limit): # check if power is static
      k += 1
    else:
      k = 0

    if k >= cycles:
      STATIC = True

    print(k)
    sleep(DATA_CYCLE)            # wait a second
  return True

def switch_heater_off():
  GPIO.output(REL1, GPIO.HIGH) # deactivate GPIO for Relais 1
  GPIO.output(REL2, GPIO.HIGH) # deactivate GPIO for Relais 2
  sleep(DATA_CYCLE)
  print("switch off heater")


# ------------------------- main -------------------------------------
## check for static power consumption
try:
  i = int(0)
  STAT_1000 = False
  STAT_2000 = False

  # only check summerized power consumption
  LC = 0; # LG by default
  logger.info("--- START to check overall power for energie exceeds ---")
  print("--- START to check overall power for energie exceeds ---")

  while True:
    # check Thermostat and wait for cooler times
    if GPIO.input(TST1):
      switch_heater_off()
      STAT_1000 = False
      print("heisz genug, wait")
      sleep(30)
      continue

    # create copy of data set
    power_old = power[:]

    print("old %i" % power[LC])
#######
    # check if data are valid
    if read_power(power) != True:
      continue

    print("new %i" % power_old[LC])
#######
    # check if data stays the same for too long
    i = 0
    while power == power_old:
      if i > 5:
        print("received to often the same data structure")
        switch_heater_off()
        STAT_1000 = False
        STAT_2000 = False
      i += 1
      # check if data are valid
      sleep(DATA_CYCLE)            # wait a second
      if read_power(power) != True:
        continue

    print(power[LC])

    # check to heat if fan and 1k heater is already on
    if STAT_1000 and (not STAT_2000) and (power[LC] <= (((L2000 - L1000) * (-6)) / 5)): # 120 % Einspeiung
      print("activate 2000 W heating modus")
      GPIO.output(REL2, GPIO.LOW)
      STAT_2000 = True
    elif STAT_1000 and STAT_2000 and (power[LC] >= ((L2000 * (-1)) / 10)): # 10 % Reserve
      print("deactivate 2000 W heating modus")
      GPIO.output(REL2, GPIO.HIGH)
      STAT_2000 = False

    # check to heat if nothing is on
    if (not STAT_1000) and (not STAT_2000) and (power[LC] <= ((L2000 * (-6)) / 5)): # 120 % Einspeiung
      print("activate 2000 W heating modus")
      GPIO.output(REL2, GPIO.LOW)
      STAT_2000 = True
    elif STAT_1000 and STAT_2000 and (power[LC] >= ((L2000 * (-1)) / 10)): # 10 % Reserve
      print("deactivate 2000 W heating modus")
      GPIO.output(REL2, GPIO.HIGH)
      STAT_2000 = False

    # check to heat to activate only fan and 1k heater
    if (not STAT_1000) and (power[LC] <= ((L1000 * (-13)) / 10)): # 130 % Einspeiung
      print("activate 1000 W heating modus")
      GPIO.output(REL1, GPIO.LOW)
      STAT_1000 = True
    elif STAT_1000 and (power[LC] >= ((L1000 * (-1)) / 10)): # 10 % Reserve
      print("deactivate 1000 W heating modus")
      GPIO.output(REL1, GPIO.HIGH)
      STAT_1000 = False


    print("")
#######
    sleep(DATA_CYCLE)

except KeyboardInterrupt:      # trap a CTRL+C keyboard interrupt
  switch_heater_off()
