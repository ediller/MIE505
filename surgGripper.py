# File containing functions relevant to the surgical tool project
# Author: Cameron Forbrigger
# Date: January 15th, 2019
import time
import numpy as np
from mathfx import *
from math import pi, sin, cos, sqrt, atan2, degrees
from PyQt5.QtCore import pyqtSignal, QMutexLocker, QMutex, QThread

def calc_field(azimuth, altitude, fieldParall):
    # Intializing vectors
    eHatR = np.zeros(3)
    eHatAz = np.zeros(3)
    eHatAl = np.zeros(3)
    eHatX = np.array([1, 0, 0])  # X-axis unit vector (^i)
    # Constant describing wrist angular deflection to perpendicular field
    # magnitude.
    mTPerRad = 0.1383 * 180 / np.pi  #[mT/rad]
    # Calculate unit vectors of the spherical coordinates
    eHatR[0] = np.cos(altitude) * np.cos(azimuth)
    eHatR[1] = np.cos(altitude) * np.sin(azimuth)
    eHatR[2] = np.sin(altitude)
    # Parallel field vector
    BParall = fieldParall * eHatR  #[mT]
    if azimuth == 0.0 and altitude == 0.0:
        # No perpendicular field
        BTotal = BParall
    else:
        # Calculate perpendicular field
        eHatAz[0] = -np.sin(azimuth)
        eHatAz[1] = np.cos(azimuth)
        eHatAl[0] = -np.sin(altitude) * np.cos(azimuth)
        eHatAl[1] = -np.sin(altitude) * np.sin(azimuth)
        eHatAl[2] = np.cos(altitude)
        # Included angle between the radial vector and the x-axis
        temp = np.cross(eHatX, eHatR)
        theta = np.arctan2(
            np.linalg.norm(temp), np.dot(eHatX, eHatR)
            )  #[rad]
        #  Field vector angle from eHatAz in the eHatAz-eHatAl plane
        phi = np.arctan2(
            np.sin(altitude) * np.cos(azimuth) / np.sin(theta),
            np.sin(azimuth) / np.sin(theta)
            )  # [rad]

        # Perpendicular field vector
        BPerp = (
            theta * mTPerRad * (np.cos(phi)*eHatAz + np.sin(phi)*eHatAl)
            )  #[mT]
        BTotal = BParall + BPerp  #[mT]
    return BTotal
