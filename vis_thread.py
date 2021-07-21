"""
=============================================================================
vis_thread.py
----------------------------------------------------------------------------
used to start a new thread of vision
=============================================================================
"""
import time
import numpy as np
from PyQt5.QtCore import pyqtSignal, QMutexLocker, QMutex, QThread


def subthreadNotDefined():
    print('Subthread not defined.')
    return


class Vis_Process_Thread(QThread): #for running vision processing
    statusSignal = pyqtSignal(str)

    def __init__(self,vision,parent=None,):
        super(Vis_Process_Thread, self).__init__(parent)
        print('in vision_process_thread init')
        self.stopped = False
        self.mutex = QMutex()
        self.vision = vision

    # def setup(self,subThreadName):
        # self._subthreadName = subThreadName
        # self.stopped = False

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    def run(self): #put my code here
        #count = 0
        # while count < 2:
            # time.sleep(1)
            # print("A Increasing")
            # count += 1
        #print('in vision_process_thread run')
        self.vision.setStateUpdate(True)
        self.vision.infiniteFrameProcess() #run vision
