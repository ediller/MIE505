import time
import numpy as np
from s826 import S826


def send_field_command(fieldOutput):
    """Command a uniform magnetic flux density output from the coil system.

    This function uses the conversion factors determined from the coil
    system calibration.
    """
    # Coil current analog output channel numbers and conversion factors in mT/V
    AO_X1 = [5, 2.801]
    AO_X2 = [1, 2.425]
    AO_Y1 = [2, 2.243]
    AO_Y2 = [6, 3.100]
    AO_Z1 = [3, 2.683]
    AO_Z2 = [7, 2.254]
    # Send voltage commands to the AO pins
    boardObj.s826_aoPin(AO_X1[0], fieldOutput[0] / 2 / AO_X1[1])
    boardObj.s826_aoPin(AO_X2[0], fieldOutput[0] / 2 / AO_X2[1])
    boardObj.s826_aoPin(AO_Y1[0], fieldOutput[1] / 2 / AO_Y1[1])
    boardObj.s826_aoPin(AO_Y2[0], fieldOutput[1] / 2 / AO_Y2[1])
    boardObj.s826_aoPin(AO_Z1[0], fieldOutput[2] / 2 / AO_Z1[1])
    boardObj.s826_aoPin(AO_Z2[0], fieldOutput[2] / 2 / AO_Z2[1])


def get_field_estimate():
    """Estimate the flux density output using the measured amplifier currents.

    This function requests the voltage measurements from the s826 analog
    inputs and converts them to estimated flux density. The conversion factors
    were determined from the coil system calibration.
    """
    # Conversion factors from measured voltage to output current for the 30A8
    # and 120A10 amplifier boards.
    measureFactor30A8 = 3.8 #[A/V]
    measureFactor120A10 = 15.9 #[A/V]
    # Coil current analog input channel numbers and conversion factors in mT/V
    AI_X1 = [4, measureFactor30A8 * 0.838]
    AI_X2 = [6, measureFactor30A8 * 0.762]
    AI_Y1 = [10, measureFactor30A8 * 0.676]
    AI_Y2 = [8, measureFactor30A8 * 0.973]
    AI_Z1 = [14, measureFactor30A8 * 0.802]
    AI_Z2 = [12, measureFactor30A8 * 0.780]
    # Read from the analog input slots on the s826 board
    boardObj.s826_aiRead()
    fieldEstimate = [0, 0, 0]
    # Convert the analog input measured voltages into estimated field values
    fieldEstimate[0] = (boardObj.ai[AI_X1[0]] * AI_X1[1]
        + boardObj.ai[AI_X2[0]] * AI_X2[1]) #[mT]
    fieldEstimate[1] = (boardObj.ai[AI_Y1[0]] * AI_Y1[1]
        + boardObj.ai[AI_Y2[0]] * AI_Y2[1]) #[mT]
    fieldEstimate[2] = (boardObj.ai[AI_Z1[0]] * AI_Z1[1]
        + boardObj.ai[AI_Z2[0]] * AI_Z2[1]) #[mT]
    return fieldEstimate


# Instantiate object for commanding the Sensoray s826 Multifunction I/O board.
boardObj = S826()
# Buffers for moving average filters.
bufLength = 50 #[samples]
bufX = np.zeros(bufLength)
bufY = np.zeros(bufLength)
bufZ = np.zeros(bufLength)
# Approximate sample period.
tSample = 0.01 #[s]
# Maximum running time.
tMax = 20 #[s]
# Initialize index of moving average filters.
index = 0
# Field to be produced by the coils
fieldOutput = [-14, 0, 0] #[mT]
send_field_command(fieldOutput)
# Begin timer.
tStart = time.time() #[s]
t = time.time() - tStart #[s]
while t < tMax:
    # Get the measured current values from the coils.
    fieldEstimate = get_field_estimate()
    # Convert measured voltages to their respective coil currents.
    bufX[index] = fieldEstimate[0] #[mT]
    bufY[index] = fieldEstimate[1] #[mT]
    bufZ[index] = fieldEstimate[2] #[mT]
    # Calculate the average of the filter buffer contents.
    fieldX = np.mean(bufX) #[A]
    fieldY = np.mean(bufY) #[A]
    fieldZ = np.mean(bufZ) #[A]
    # Print the results in a clean tabular format at the command line.
    print('t: ', ('{0:0.2f}'.format(t)).rjust(4), 's; ', end=' ')
    print('Bx: ', ('{0:.1f}'.format(fieldX)).rjust(5), ' mT; ', end=' ')
    print('By: ', ('{0:.1f}'.format(fieldY)).rjust(5), ' mT; ', end=' ')
    print('Bz: ', ('{0:.1f}'.format(fieldZ)).rjust(5), ' mT.')
    # Wait for one sample period
    time.sleep(tSample)
    # Read the current time since starting
    t = time.time() - tStart
    # Increment buffer and loop back to 0 if it exceeds bufLength
    index = (index+1) % bufLength

# Set all outputs to zero (clear coil currents)
fieldOutput = [0, 0, 0] #[mT]
send_field_command(fieldOutput)
# Close communication with the s826 board
boardObj.s826_close()
