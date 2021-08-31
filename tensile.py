import RPi.GPIO as gpio
import time
from hx711 import HX711
import numpy as np

class tensile:
    "This class reads, calibrates, and calculates the force from the load cell and controls motor speed and direction"
    def __init__(self):
        #######################################################
        # Initialize load cell                                #
        #######################################################
        gpio.setwarnings(False) # turn off gpio warnings
        # initialize GPIO pins
        self.hx711 = HX711(dout_pin = 26, pd_sck_pin = 19, channel = 'A', gain =64)
        # reset the hx711
        self.hx711.reset()
        self.init_measure = np.mean(self.hx711.get_raw_data(3))
        
        #######################################################
        #  Initialize motor                                   #
        #######################################################
        #GPIO pins for motor and motor encoder
        gpio.setmode(gpio.BCM)
        
        self.dirPIN =  16 # motor direction pin
        self.stepPIN = 20 # motor step pin
        
        gpio.setup(self.dirPIN,gpio.OUT) # motor direction PIN setup
        gpio.setup(self.stepPIN,gpio.OUT) # motor step PIN setup
        
        gpio.output(self.dirPIN,gpio.HIGH) # direction of the motor initially set clockwise
       
        
    def load_cal(self):
        "returns the scale ratio for calibration" 
        # calibration mass user input
        cal_mass = input('Enter known mass in grams:')
        print('Place mass now')
        time.sleep(10)
        # calbration reading from HX711
        cal_reading = self.hx711.get_raw_data(3)
        average_cal_reading = np.mean(cal_reading)
        # scale ratio
        scale_ratio = (np.float(cal_mass))/(average_cal_reading-80323)
        
        return scale_ratio, self.init_measure
    
    def load_force_reading(self):
        "returns the force reading in Newtons"
        scale_ratio = 0.0039476174596450751
        measures = self.hx711.get_raw_data(3) # measure average reading
        mass = (np.mean(measures)-80323)*scale_ratio #mass calculation
        force = 9.81*mass/1000 # force calculation in Newtons
        return force
    
    def setSpeed(self,speed,direction):
        "input in a speed value (mm/min) and 0 or 1 direction and moves the motor"
        # motor has 200 steps per revolution, pitch is ~5mm
        max_speed = 30 # set max_speed
        min_speed = 0.5 # set min_speed
        
        if speed >= 30:
            speed = 30 # if the specified speed is greater than 30mm/min then set to max_speed
        elif speed <= 0.5:
            speed = 0.5 # if the specified speed is lower than or equal 0, then set to min_speed
        else:
            speed = speed # anything in between is ok
        
        delay = (5/200)*(1/(speed/60))# calculate delay from speed in seconds
        
        try:
                self.motor_change_dir(direction) # change to desired direction 0 or 1
                self.motor_step() # take a step
                time.sleep(delay)    
                return delay
            
        except KeyboardInterrupt:
            self.stop()     
    
    def motor_change_dir(self,direction):
        "input a direction value of 0 or 1 if 0 then CW if 1 than CCW"
        gpio.output(self.stepPIN,gpio.LOW) # stop the motor after no force detected

        if direction == 0:
            gpio.output(self.dirPIN, gpio.LOW) # change the direction of the motor to CW
        else:
            gpio.output(self.dirPIN, gpio.HIGH) # change the direction of the motor to CCW
            
    def motor_step(self):
        "motor moves one step"
        gpio.output(self.stepPIN,gpio.HIGH)
        gpio.output(self.stepPIN,gpio.LOW)
    
    def motor_reset(self,distance):
        "reset the motor to starting position"
        # stop the motor if directed by the user
        gpio.output(self.stepPIN,gpio.LOW)
        # change direction
        gpio.output(self.dirPIN, gpio.LOW)
        # travel back the initial distance
        mm_per_step = 1.8*5/360
        # convert distance to steps
        num_steps = int(distance/mm_per_step)
        for i in range(1,num_steps+1):
            gpio.output(self.stepPIN,gpio.HIGH)
            gpio.output(self.stepPIN,gpio.LOW)
            time.sleep(0.25)
        

