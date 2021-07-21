import time
import numpy as np
from s826 import S826


def send_voltage_command(voltOutput):
    """Send voltage commands to the coil system.

    Given a list of 6 voltages. The order of the coils is X1, X2, Y1, Y2, Z1,
    Z2.
    """
    # Coil current analog output channel numbers
    AO_X1 = 5
    AO_X2 = 1
    AO_Y1 = 2
    AO_Y2 = 6
    AO_Z1 = 3
    AO_Z2 = 7
    AO_S1 = 0
    AO_S2 = 4
    # Send commands to the AO pins
    boardObj.s826_aoPin(AO_X1, voltOutput[0])
    boardObj.s826_aoPin(AO_X2, voltOutput[1])
    boardObj.s826_aoPin(AO_Y1, voltOutput[2])
    boardObj.s826_aoPin(AO_Y2, voltOutput[3])
    boardObj.s826_aoPin(AO_Z1, voltOutput[4])
    boardObj.s826_aoPin(AO_Z2, voltOutput[5])


def get_coil_currents():
    """Calculate the coil currents from the measured analog input voltages.

    Requests the measured voltages from the analog input slots and converts
    them to measured current values. The order of the coils is X1, X2, Y1, Y2,
    Z1, Z2.
    """
    # Conversion factors from measured voltage to output current for the 30A8
    # and 120A10 amplifier boards.
    measureFactor30A8 = 3.8 #[A/V]
    measureFactor120A10 = 15.9 #[A/V]
    # Coil current analog input channel numbers and conversion factors
    AI_X1 = [4, measureFactor30A8]
    AI_X2 = [6, measureFactor30A8]
    AI_Y1 = [10, measureFactor30A8]
    AI_Y2 = [8, measureFactor30A8]
    AI_Z1 = [14, measureFactor30A8]
    AI_Z2 = [12, measureFactor30A8]
    # Read from the analog input slots on the s826 board
    boardObj.s826_aiRead()
    currents = [0, 0, 0, 0, 0, 0]
    # Convert the analog input measured voltages into measured current values
    currents[0] = boardObj.ai[AI_X1[0]] * AI_X1[1] #[A]
    currents[1] = boardObj.ai[AI_X2[0]] * AI_X2[1] #[A]
    currents[2] = boardObj.ai[AI_Y1[0]] * AI_Y1[1] #[A]
    currents[3] = boardObj.ai[AI_Y2[0]] * AI_Y2[1] #[A]
    currents[4] = boardObj.ai[AI_Z1[0]] * AI_Z1[1] #[A]
    currents[5] = boardObj.ai[AI_Z2[0]] * AI_Z2[1] #[A]
    return currents


# Instantiate object for commanding the Sensoray s826 Multifunction I/O board.
boardObj = S826()
# Buffers for moving average filters.
bufLength = 50 #[samples]
bufX1 = np.zeros(bufLength)
bufX2 = np.zeros(bufLength)
bufY1 = np.zeros(bufLength)
bufY2 = np.zeros(bufLength)
bufZ1 = np.zeros(bufLength)
bufZ2 = np.zeros(bufLength)
bufS1 = np.zeros(bufLength)
bufS2 = np.zeros(bufLength)
# Approximate sample period.
tSample = 0.01 #[s]
# Maximum running time.
tMax = 20 #[s]
# Initialize index of moving average filters.
index = 0
# Voltage applied to the amplifiers by the s826 board.
# 0: X1, 1: X2, 2: Y1, 3: Y2, 4: Z1, 5: Z2
voltOutput = [0, 0, 0, 0, 0, 0] #[V]
send_voltage_command(voltOutput)
# Begin timer.
tStart = time.time() #[s]
t = time.time() - tStart #[s]
while t < tMax:
    # Get the measured current values from the coils.
    currents = get_coil_currents()
    # Convert measured voltages to their respective coil currents.
    bufX1[index] = currents[0] #[A]
    bufX2[index] = currents[1] #[A]
    bufY1[index] = currents[2] #[A]
    bufY2[index] = currents[3] #[A]
    bufZ1[index] = currents[4] #[A]
    bufZ2[index] = currents[5] #[A]
    # Calculate the average of the filter buffer contents.
    currentX1 = np.mean(bufX1) #[A]
    currentX2 = np.mean(bufX2) #[A]
    currentY1 = np.mean(bufY1) #[A]
    currentY2 = np.mean(bufY2) #[A]
    currentZ1 = np.mean(bufZ1) #[A]
    currentZ2 = np.mean(bufZ2) #[A]
    # Print the results in a clean tabular format at the command line.
    print('t: ', ('{0:0.2f}'.format(t)).rjust(3), 's; ', end=' ')
    print('+X: ', ('{0:.2f}'.format(currentX1)).rjust(5), ' A; ', end=' ')
    print('-X: ', ('{0:.2f}'.format(currentX2)).rjust(5), ' A; ', end=' ')
    print('+Y: ', ('{0:.2f}'.format(currentY1)).rjust(5), ' A; ', end=' ')
    print('-Y: ', ('{0:.2f}'.format(currentY2)).rjust(5), ' A; ', end=' ')
    print('+Z: ', ('{0:.2f}'.format(currentZ1)).rjust(5), ' A; ', end=' ')
    print('-Z: ', ('{0:.2f}'.format(currentZ2)).rjust(5), ' A.')
    # Wait for one sample period
    time.sleep(tSample)
    # Read the current time since starting
    t = time.time() - tStart
    # Increment buffer and loop back to 0 if it exceeds bufLength
    index = (index+1) % bufLength
# Set all outputs to zero (clear coil currents)
voltOutput = [0, 0, 0, 0, 0, 0] #[V]
send_voltage_command(voltOutput)
# Close communication with the s826 board
boardObj.s826_close()
