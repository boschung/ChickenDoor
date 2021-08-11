# chickenDoor.py 
# PWM servo output 1-2 ms out of 20 ms
# input Foto-Resistor and time
# nice DOC: https://docs.micropython.org/en/latest/esp32/quickref.html#pins-and-gpio
# Start:     ampy --port com3 put chickenDoor.py /main.py
# Stopp it:  ampy --port com3 rm main.py
# import pytest 

from machine import Pin, ADC, PWM, RTC
import machine
import time   

# Debug values for fast driving and reaction
loopTime_ms = 1000*60*5
detectionTimeBrake_ms = 1000*60*5
detectionTimeMorningBrake_ms = 1000*60*5
driveTime_ms = 1000*8
moveDelay_ms = 1000*8
startuptimings_ms = 1000*20

# Outputs ----------------------------------------
PIN2_LED = Pin(2, Pin.OUT)    # create output pin on GPIO2 LED Blue

# Inputs ----------------------------------------
## Sensor

# 3.3V pin33 
#  |
#  RFoto PDVP8103 (20k-0.5M) --> (1.1V - 0.66V) = (Bright-Dark)
#  |---------------------- threshold  pin32
#  R10k
#  |
#  GND
PIN32_FOTOSENS = ADC(Pin(32))          # create ADC object on ADC pin
#PIN32_FOTOSENS.read()                  # read value, 0-4095 across voltage range 0.0v - 1.0v
PIN32_FOTOSENS.atten(ADC.ATTN_11DB)    # set 11dB input attenuation (voltage range roughly 0.0v - 3.6v)

dayThreshold = 300
nightThreshold = 250 

### Detect Day State by foto sensor 
stateDay = 1
stateNight = 0

state = stateNight
lastState = stateNight

adcValue = 0

# Class Servo Door ----------------------------------------

class Door:
    # Servo pwm settings ----------------------------------------
    # 1 ms CW, 1.5 ms middle, 2 ms CCW
    
    def __init__(self):
        self.PIN13_SERVO = 13
        # PWM Calculations
        self.duty100= 1023
        self.period = 0.020 
        self.frequency = int(1/self.period)
        self.time_ccw = 0.0024
        self.time_cw = 0.001
        self.maxPWM_CCW = int(self.duty100/self.period * self.time_ccw)  #51 102
        self.minPWM_CW = int(self.duty100/self.period * self.time_cw)
        self.delta1percent = int(self.maxPWM_CCW - self.minPWM_CW) /100
    
    def close(self):
        PIN2_LED.on()
        PWM(Pin(self.PIN13_SERVO), freq=self.frequency, duty=self.minPWM_CW)
        time.sleep_ms(moveDelay_ms)
        PWM(Pin(self.PIN13_SERVO), freq=self.frequency, duty=0)

    def open(self):
        PIN2_LED.off()
        PWM(Pin(self.PIN13_SERVO), freq=self.frequency, duty=self.maxPWM_CCW)
        time.sleep_ms(moveDelay_ms)
        PWM(Pin(self.PIN13_SERVO), freq=self.frequency, duty=0)


# Statemachine  ----------------------------------------

def stateMachine():
    print(str(state) + ";" + str(lastState) + ";" +str(adcValue)+ ";" +str(rtc.datetime()))
    stateChanged = 0
    if lastState != state :
        stateChanged = 1 
    if stateChanged == 1:
        if state == stateNight:
            myChickenDoor.close()
        if state == stateDay:
            myChickenDoor.open()
    return 0

# Pre settings of ChickenDoor ----------------------------------------

myChickenDoor = Door()

# Real TIme Clock
rtc = RTC()
#              Y    M    D  D(auto) h   m  s  ms 
rtc.datetime((2021, 5, 30,  0,    10, 23, 0, 0))


# Startup Time to get the Capacitors loaded
PIN2_LED.on()
time.sleep_ms(startuptimings_ms)
PIN2_LED.off()

# Move Test
myChickenDoor.open()
time.sleep_ms(startuptimings_ms) 
myChickenDoor.close()


# Header
print("Start at: " + str(rtc.datetime()))
print("state;lastState;adcValue;datetime")

# Main of ChickenDoor ----------------------------------------

while 1:
    adcValue = PIN32_FOTOSENS.read()                  # read value using the newly configured attenuation and width
    if adcValue > dayThreshold:
        time.sleep_ms(detectionTimeMorningBrake_ms)
        adcValue = PIN32_FOTOSENS.read() 
        if adcValue > dayThreshold:
            lastState = state
            state = stateDay
    if adcValue < nightThreshold:
        time.sleep_ms(detectionTimeBrake_ms)
        adcValue = PIN32_FOTOSENS.read() 
        if adcValue < nightThreshold:
            lastState = state
            state = stateNight
    stateMachine()
    time.sleep_ms(loopTime_ms) #few minutes
