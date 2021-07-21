from ctypes import cdll, c_int, c_uint, byref
import numpy as np
import time
# Wrapping the C library provided by Sensoray for the s826 board.
#s826dll = cdll.LoadLibrary("./lib826_64.so") #disabled Eric
# Sensoray s826 board number.
BOARD = 0
# Minimum voltages and voltage ranges for rangeCode = 0, 1, 2, 3.
RANGE_PARAM = [[0,5], [0,10], [-5,10], [-10,20]]
# Analog input maximum voltage for aiRangeCode = 0, 1, 2, 3.
AI_RANGE_PARAM = [10, 5, 2, 1]
# AI channel numbers corresponding to each timeslot.
SLOT_CHAN = [0, 2, 4, 6, 8, 10, 12, 14]

class S826(object):
    def __init__(self):
        # Default values for the lower voltage and voltage range of the
        # analog output channels.
        self.lowerV = [-5,-5,-5,-5,-5,-5,-5,-5]
        self.rangeV = [10,10,10,10,10,10,10,10]
        # Default values for the maximum measurable voltage on the analog input
        # slots.
        self.aiMaxV = [10,10,10,10,10,10,10,10]
        # Initial values for the measured analog input channels.
        self.ai = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        errCode = 1#self.s826_init()
        if errCode < 1:
            return errCode
        self.s826_initRange()
        self.s826_initAnalogInputs()

    def s826_init(self):
        """Open communication with the s826 board."""
        errCode = 1#s826dll.S826_SystemOpen() #disabled Eric by hardcoding to 1
        if errCode < 0:
            print('Cannot initialize s826 board. ')
            self.s826_errorInterpreter(errCode)
        elif errCode == 0:
            print('Cannot detect S826 board (Error code {}).'.format(errCode))
            self.s826_close()
        else:
            print('S826 initialized.')
        return errCode

    def s826_close(self):
        """Close communication with the s826 board.

        Note: this method does not clear the voltage outputs. Make sure
        the voltage outputs are set to zero before closing communication.
        """
        s826dll.S826_SystemClose()

    def s826_initRange(self):
        """Initialize the voltage ranges of all s826 analog outputs."""
        # Configure 8 analog outputs
        for i in range(8):
            self.s826_setRange(i,2)

    def s826_initAnalogInputs(self):
        """Configure the s826 analog input slots.

        The present configuration is intended for reading from the 8 AMC
        amplifiers.
        """
        # ----- AMC 30A8 -----
        # Peak current: 30 A, Monitor conversion factor: 3.8 A/V
        # 30 A / 3.8 A/V = 7.89 V maximum
        # ----- AMC 120A10 -----
        # Peak current: 120 A, Monitor conversion factor: 15.9 A/V
        # 120 A / 15.9 A/V = 7.55 V maximum
        # Expected range of measurement is set by the range code
        #   0: +/-10 V;  1: +/-5 V;  2: +/-2 V;  3: +/-1 V
        aiRangeCode = 0
        # Settling time before recording measurement
        tSettle = 10 # microseconds
        # Configure 8 analog input timeslots
        
        # Skip sampling all but the first 8 timeslots
        slotList = 0x00ff
        

    # ======================================================================
    # rangeCode: 0: 0 +5V; 1: 0 +10V; 2: -5 +5V; 3:-10 +10V.
    # ======================================================================
    def s826_setRange(self,chan,rangeCode):
        """Set the range of one of the s826 analog output channels.

        It also stores the corresponding lower voltage and range as
        object properties.
        """
        self.lowerV[chan] = RANGE_PARAM[rangeCode][0]
        self.rangeV[chan] = RANGE_PARAM[rangeCode][1]
        #s826dll.S826_DacRangeWrite(BOARD, chan, rangeCode, 0) #disabled Eric

    # ======================================================================
    # Set 1 AO channel.
    # chan : DAC channel # in the range 0 to 7.
    # outputV: Desired analog output voltage (can be positive and negative).
    # ======================================================================
    def s826_aoPin(self,chan,outputV):
        """Command an analog output from the specified channel."""
        lowerV = self.lowerV[chan]
        rangeV = self.rangeV[chan]
        setpoint = int((outputV-lowerV)/rangeV*0xffff)
        #s826dll.S826_DacDataWrite(BOARD,chan,setpoint,0)

    def s826_aiRead(self):
        """Read from configured s826 analog input slots.

        The measured voltages are stored as object properties.
        """
        # Creating buffer classes to store the AI data
        cIntBuffer = c_int * 16
        cUIntBuffer = c_uint * 16
        # Instantiating buffers
        buf = cIntBuffer()
        tstamp = cUIntBuffer()
        # Slotlist for the first 8 slots (bitflags to indicate slots of
        # interest).
        slotlist = c_uint(0x00ff)
        # Maximum time to wait for new values. Zero means return immediately.
        tmax = 0 # microseconds
        # Note: S826_AdcRead appears to return -3 even when it is working
        # properly.
        errCode =0
        #errCode = s826dll.S826_AdcRead(
        #    BOARD, byref(buf), byref(tstamp), byref(slotlist), tmax
        #    )
        for slotNum in range(8):
            aiValue = np.int16(buf[slotNum] & 0x0000ffff)
            self.ai[SLOT_CHAN[slotNum]] = (aiValue/0x8fff)*self.aiMaxV[slotNum]
        # flag[0] = (buf[0] & 0x00800000) >> 23
        # burstNum[0] = (buf[0] & 0xFF000000) >> 24
        # print(self.ai)

    def s826_errorInterpreter(self,errCode):
        """Interpret s826 error codes.

        This method interprets the error codes returned by most of the
        s826 board functions and prints the corresponding error message
        from the s826 manual.
        """
        # List of standard error messages from Sensoray
        errMsg = [
            's826: No errors (0).',
            's826: Invalid board number (-1).',
            's826: Illegal argument value (-2).',
            's826: Device was busy or unavailable, or blocking function timed out (-3).',
            's826: Blocking function was canceled (-4).',
            's826: Driver call failed (-5).',
            's826: ADC trigger occurred while previous conversion burst was in progress (-6).',
            's826: Unknown error (-7).',
            's826: Unknown error (-8).',
            's826: Two s826 boards are set to the same board number. Change DIP switch settings (-9).',
            's826: Addressed board is not open (-10).',
            's826: Failed to create internal mutex (-11).',
            's826: Failed to map board into memory space (-12).',
            's826: Failed to allocate memory (-13).',
            's826: Unknown error (-14).',
            's826: Counter channel\'s snapshot FIFO overflowed (-15).'
            's826: Error specific to the operating system. Contact Sensoray (-1xx).'
            ]
        if errCode < 0:
            if errCode < -15:
                errIndex = 16
            else:
                errIndex = -errCode
            print(errMsg[errIndex])
        return errCode
