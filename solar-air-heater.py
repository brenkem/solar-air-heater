#!/usr/bin/python

import RPi.GPIO as GPIO
from time import sleep             # lets us have a delay

# 900
# 1800
L1000 = 900  # power of 1000 W mode
L2000 = 1800 # power of 2000 W mode

LT = 1600 # trigger power off heater

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
LC = int(); # connected "PHASE"
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

def detect_PHASE():
  LC = int(0)

  while LC == 0:
    # save power and start heater and wait 2 cycles
    GPIO.output(REL1, GPIO.LOW)
    GPIO.output(REL2, GPIO.LOW)
    sleep(DATA_CYCLE * 2)

    # check if data are valid
    while read_power(power) != True:
      continue

    calc_diff_power(power_diff, power, power_old)
    print(power_diff)

    # deactivate heating
    GPIO.output(REL1, GPIO.HIGH)
    GPIO.output(REL2, GPIO.HIGH)

    # detect connected "PHASE"
    for i in range(L1, L3+1): # from L1 to L3
      if power_diff[i] > LT: # check trigger to detect "PHASE"
        LC = i;
        print("PHASE auf %i" % LC);
        return LC

    print("Failed to detect PHASE. Try again.")
    sleep(10)


# dectect PHASE
## check for static power consumption
try:
  i = int(0)

  # check if power consumption is in the defines limit for defines cycles
#  detect_static_power_consumption(5, 20) # 20 Watt
  detect_static_power_consumption(1, 20) # 20 Watt

  # detect the 1 "PHASE" of the 3 house "PHASEN"
  LC = detect_PHASE()
  sleep(DATA_CYCLE * 2)
  print("--- START to check PH %i for energie exceeds ---" % LC)

  while True:
    # check Thermostat and wait for cooler times
    if GPIO.input(TST1) == ??????
      sleep 30
      continue

    # create copy of data set
    power_old = power[:]

    # check if data are valid
    if read_power(power) != True:
      continue

    while power == power_old:
      if i > 5:
        i = 0
        continue
      i += 1
      # check if data are valid
      if read_power(power) != True:
        continue

    print(power[LC])

    if power[LC] >= ((L1000 * 6) / 5): # 120 %
      print("activate 1000 W heating modus")
      GPIO.output(REL1, GPIO.LOW)

    if power[LC] >= ((L2000 * 6) / 5): # 120 %
      print("activate 2000 W heating modus")
      GPIO.output(REL2, GPIO.LOW)

    print("")
    sleep(DATA_CYCLE)            # wait a second


#    GPIO.output(REL1, GPIO.LOW)  # set GPIO for Relais 1
#    GPIO.output(REL2, GPIO.HIGH) # deactivate GPIO for Relais 2
#    sleep(DATA_CYCLE)            # wait a second
#    GPIO.output(REL1, GPIO.HIGH) # deactivate GPIO for Relais 1
#    GPIO.output(REL2, GPIO.LOW)  # set GPIO for Relais 2
#    sleep(DATA_CYCLE)            # wait a second

except KeyboardInterrupt:      # trap a CTRL+C keyboard interrupt
  GPIO.output(REL1, GPIO.HIGH) # deactivate GPIO for Relais 1
  GPIO.output(REL2, GPIO.HIGH) # deactivate GPIO for Relais 2
#  GPIO.cleanup()               # resets all GPIO ports used by this program
