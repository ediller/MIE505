

class FieldManager(object):
    def __init__(self, dac):
        # Coil analog output channel numbers.
        self.aoPinX1 = 5
        self.aoPinX2 = 1
        self.aoPinY1 = 2
        self.aoPinY2 = 6
        self.aoPinZ1 = 3
        self.aoPinZ2 = 7
        # Coil analog input channel numbers.
        self.aiPinX1 = 4
        self.aiPinX2 = 6
        self.aiPinY1 = 10
        self.aiPinY2 = 8
        self.aiPinZ1 = 14
        self.aiPinZ2 = 12
        # Coil analog output conversion factors determined from coil
        # calibration.
        self.aoFactorX1 = 2.801 #[mT/V]
        self.aoFactorX2 = 2.425 #[mT/V]
        self.aoFactorY1 = 2.243 #[mT/V]
        self.aoFactorY2 = 3.100 #[mT/V]
        self.aoFactorZ1 = 2.683 #[mT/V]
        self.aoFactorZ2 = 2.254 #[mT/V]
        # Coil analog input conversion factors determined from coil
        # calibration.
        self.aiFactorX1 = 0.838 #[mT/A]
        self.aiFactorX2 = 0.762 #[mT/A]
        self.aiFactorY1 = 0.676 #[mT/A]
        self.aiFactorY2 = 0.973 #[mT/A]
        self.aiFactorZ1 = 0.802 #[mT/A]
        self.aiFactorZ2 = 0.780 #[mT/A]
        # Conversion factors from measured voltage to output current for the
        # Advanced Motion Controls 30A8 and 120A10 servo driver boards.
        measureFactor30A8 = 3.8 #[A/V]
        measureFactor120A10 = 15.9 #[A/V]
        # Coil analog input conversion factor from measured voltage to current
        self.aiVoltToCurrent = measureFactor30A8 #[A/V]
        # Initial requested field values
        self.bxSetpoint = 0 #[mT]
        self.bySetpoint = 0 #[mT]
        self.bzSetpoint = 0 #[mT]
        # Initial field values estimated from measured coil currents
        self.bxEstimate = 0 #[mT]
        self.byEstimate = 0 #[mT]
        self.bzEstimate = 0 #[mT]
        # Initial coil currents
        self.ix1 = 0 #[A]
        self.ix2 = 0 #[A]
        self.iy1 = 0 #[A]
        self.iy2 = 0 #[A]
        self.iz1 = 0 #[A]
        self.iz2 = 0 #[A]
        # s826 board
        self.dac = dac

    def setX(self, mT):
        """Generate a zero-gradient magnetic flux density in the x-direction.

        The requested field is split evenly between the two x-direction
        Helmholtz coils.
        """
        self.dac.s826_aoPin(self.aoPinX1, mT / 2 / self.aoFactorX1)
        self.dac.s826_aoPin(self.aoPinX2, mT / 2 / self.aoFactorX2)
        self.bxSetpoint = mT

    def setY(self, mT):
        """Generate a zero-gradient magnetic flux density in the y-direction.

        The requested field is split evenly between the two y-direction
        Helmholtz coils.
        """
        self.dac.s826_aoPin(self.aoPinY1, mT / 2 / self.aoFactorY1)
        self.dac.s826_aoPin(self.aoPinY2, mT / 2 / self.aoFactorY2)
        self.bySetpoint = mT

    def setZ(self, mT):
        """Generate a zero-gradient magnetic flux density in the z-direction.

        The requested field is split evenly between the two z-direction
        Helmholtz coils.
        """
        self.dac.s826_aoPin(self.aoPinZ1, mT / 2 / self.aoFactorZ1)
        self.dac.s826_aoPin(self.aoPinZ2, mT / 2 / self.aoFactorZ2)
        self.bzSetpoint = mT

    def setXYZ(self, x_mT, y_mT, z_mT):
        """Generate a zero-gradient magnetic flux density in xyz."""
        self.setX(x_mT)
        self.setY(y_mT)
        self.setZ(z_mT)

    def setXGradient(self, mT):
        """Generate a flux density x-direction gradient.

        mT is a measurement of current in the coil. It has nothing to do
        with actual flux density.
        """
        if mT > 0:
            self.dac.s826_aoPin(self.aoPinX1, mT / self.aoFactorX1)
        else:
            self.dac.s826_aoPin(self.aoPinX2, mT / self.aoFactorX2)
        self.bxSetpoint = 0

    def setYGradient(self, mT):
        """Generate a flux density y-direction gradient.

        mT is a measurement of current in the coil. It has nothing to do
        with actual flux density.
        """
        if mT > 0:
            self.dac.s826_aoPin(self.aoPinY1, mT / self.aoFactorY1)
        else:
            self.dac.s826_aoPin(self.aoPinY2, mT / self.aoFactorY2)
        self.bySetpoint = 0

    def setZGradient(self, mT):
        """Generate a flux density x-direction gradient.

        mT is a measurement of current in the coil. It has nothing to do
        with actual flux density.
        """
        if mT > 0:
            self.dac.s826_aoPin(self.aoPinZ1, mT / self.aoFactorZ1)
        else:
            self.dac.s826_aoPin(self.aoPinZ2, mT / self.aoFactorZ2)
        self.bzSetpoint = 0
    def getXYZ(self): #fake estimate
        # Calculate an estimate of the magnetic flux density in mT from the
        # measured coil currents.
        self.bxEstimate = self.bxSetpoint
        self.byEstimate = self.bySetpoint
        self.bzEstimate = self.bzSetpoint
    def getXYZ_old(self):
        """Estimate the flux density in xyz using measured coil currents."""
        self.dac.s826_aiRead()
        # Calculate coil currents from measured analog input voltages.
        self.ix1 = self.dac.ai[self.aiPinX1] * self.aiVoltToCurrent #[A]
        self.ix2 = self.dac.ai[self.aiPinX2] * self.aiVoltToCurrent #[A]
        self.iy1 = self.dac.ai[self.aiPinY1] * self.aiVoltToCurrent #[A]
        self.iy2 = self.dac.ai[self.aiPinY2] * self.aiVoltToCurrent #[A]
        self.iz1 = self.dac.ai[self.aiPinZ1] * self.aiVoltToCurrent #[A]
        self.iz2 = self.dac.ai[self.aiPinZ2] * self.aiVoltToCurrent #[A]
        # Calculate an estimate of the magnetic flux density in mT from the
        # measured coil currents.
        self.bxEstimate = (self.ix1*self.aiFactorX1 + self.ix2*self.aiFactorX2)
        self.byEstimate = (self.iy1*self.aiFactorY1 + self.iy2*self.aiFactorY2)
        self.bzEstimate = (self.iz1*self.aiFactorZ1 + self.iz2*self.aiFactorZ2)
