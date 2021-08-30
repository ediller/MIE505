from PyQt5 import uic
from PyQt5.QtCore import QTimer, Qt, pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from fieldManager import FieldManager
from vision import Vision
from s826 import S826 #OLD when using S826 DAQ hardware
from tensile import tensile
from subThread import SubThread
from vis_thread import Vis_Process_Thread
from realTimePlot import CustomFigCanvas
import syntax
import numpy as np
import time
import os # added here

#=========================================================
# UI Config
#=========================================================
qtCreatorFile = "mainwindow.ui"
#qtCreatorFile = "testwindow.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
#=========================================================
# Creating instances of fieldManager, Camera, and Tensile tester
#=========================================================
field = FieldManager(S826()) #OLD when using S826 DAQ board
vision = Vision()
tensile = tensile()
# to use 1 camera only, comment out this line:    vision2 = ...
#=========================================================
# Creating instances of PS3 controller
#=========================================================
# from PS3Controller import DualShock
# joystick = DualShock()
# to disable controller comment out these 2 lines
# to disable controller comment out these 2 lines
#=========================================================
# a class that handles the signal and callbacks of the GUI
#=========================================================
class GUI(QMainWindow,Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self,None,Qt.WindowStaysOnTopHint)
        Ui_MainWindow.__init__(self)
        self.updateRate = 150 # (ms) update rate of the GUI, vision, plot
        self.setupUi(self)
        self.setupTimer()
        
        self.setupSubThread(field,vision,tensile)
        

        # comment out this line if you don't want a preview window
        self.setupRealTimePlot()

        
        self.connectSignals()
        self.linkWidgets()
        self.initDataBuffers()
        
        self.on_btn_refreshFilterRouting() #click "refresh" once

    #=====================================================
    # [override] terminate the subThread and clear currents when closing the
    # window
    #=====================================================
    def closeEvent(self,event):
        self.thrd.stop()
        self.vision_process_thread.stop()
        self.timer.stop()
        vision.closeCamera()
        try:
            vision2
        except NameError:
            pass
        else:
            vision2.closeCamera()
        try:
            joystick
        except NameError:
            pass
        else:
            joystick.quit()
        self.clearField()
        event.accept()

    #=====================================================
    # QTimer handles updates of the GUI, run at 60Hz
    #=====================================================
    def setupTimer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.updateRate) # msec

    def update(self):
        vision.updateFrame() #Eric made the acquisition/processing part of this its own thread
        try:
            vision2
        except NameError:
            pass
        else:
            vision2.updateFrame()
        try:
            self.realTimePlot
        except AttributeError:
            pass
        else:
            self.updatePlot()
        try:
            joystick
        except NameError:
            pass
        else:
            joystick.update()
        
        try: #added for tensile tester
            self.realTimePlot2
        except AttributeError:
            pass
        else:
            self.updatePlot2()

    #=====================================================
    # Connect buttons etc. of the GUI to callback functions
    #=====================================================
    def connectSignals(self):
        # General Control Tab
        self.dsb_x.valueChanged.connect(self.setFieldXYZ)
        self.dsb_y.valueChanged.connect(self.setFieldXYZ)
        self.dsb_z.valueChanged.connect(self.setFieldXYZ)
        self.btn_clearCurrent.clicked.connect(self.clearField)
        self.dsb_xGradient.valueChanged.connect(self.setFieldXYZGradient)
        self.dsb_yGradient.valueChanged.connect(self.setFieldXYZGradient)
        self.dsb_zGradient.valueChanged.connect(self.setFieldXYZGradient)
        # Vision Tab
        self.highlighter = syntax.Highlighter(self.editor_vision.document())
        self.chb_bypassFilters.toggled.connect(self.on_chb_bypassFilters)
        self.btn_refreshFilterRouting.clicked.connect(
            self.on_btn_refreshFilterRouting
            )
        self.btn_snapshot.clicked.connect(self.on_btn_snapshot)
        self.dsb_brightness.valueChanged.connect(self.on_setBrightness)
        self.dsb_screenWidth.valueChanged.connect(self.on_screenWidth)
        #self.cbb_resolution.currentTextChanged.connect(self.on_setResolution)
        self.btn_startVideo.clicked.connect(self.on_btn_startVideo)
        # object detection
        self.chb_objectDetection.toggled.connect(self.on_chb_objectDetection)

        # Subthread Tab
        self.cbb_subThread.currentTextChanged.connect(self.on_cbb_subThread)
        self.chb_startStopSubthread.toggled.connect(
            self.on_chb_startStopSubthread
            )
        self.dsb_subThreadParam0.valueChanged.connect(self.thrd.setParam0)
        self.dsb_subThreadParam1.valueChanged.connect(self.thrd.setParam1)
        self.dsb_subThreadParam2.valueChanged.connect(self.thrd.setParam2)
        self.dsb_subThreadParam3.valueChanged.connect(self.thrd.setParam3)
        self.dsb_subThreadParam4.valueChanged.connect(self.thrd.setParam4)
        
        # tensile Tab
        self.btn_adjustleft.clicked.connect(self.move_left)
        self.btn_adjustright.clicked.connect(self.move_right)
        self.btn_export.clicked.connect(self.on_export)
                                
        


    #=====================================================
    # Link GUI elements
    #=====================================================
    def linkWidgets(self):
        # link slider to doubleSpinBox
        self.dsb_x.valueChanged.connect(
            lambda value: self.hsld_x.setValue(int(value*100))
            )
        self.dsb_y.valueChanged.connect(
            lambda value: self.hsld_y.setValue(int(value*100))
            )
        self.dsb_z.valueChanged.connect(
            lambda value: self.hsld_z.setValue(int(value*100))
            )
        self.hsld_x.valueChanged.connect(
            lambda value: self.dsb_x.setValue(float(value/100))
            )
        self.hsld_y.valueChanged.connect(
            lambda value: self.dsb_y.setValue(float(value/100))
            )
        self.hsld_z.valueChanged.connect(
            lambda value: self.dsb_z.setValue(float(value/100))
            )

        self.dsb_xGradient.valueChanged.connect(
            lambda value: self.hsld_xGradient.setValue(int(value*100))
            )
        self.dsb_yGradient.valueChanged.connect(
            lambda value: self.hsld_yGradient.setValue(int(value*100))
            )
        self.dsb_zGradient.valueChanged.connect(
            lambda value: self.hsld_zGradient.setValue(int(value*100))
            )
        self.hsld_xGradient.valueChanged.connect(
            lambda value: self.dsb_xGradient.setValue(float(value/100))
            )
        self.hsld_yGradient.valueChanged.connect(
            lambda value: self.dsb_yGradient.setValue(float(value/100))
            )
        self.hsld_zGradient.valueChanged.connect(
            lambda value: self.dsb_zGradient.setValue(float(value/100))
            )
    #=====================================================
    # Thread Example
    #=====================================================
    def setupSubThread(self,field,vision,tensile,joystick=None):
        if joystick:
            self.thrd = SubThread(field,vision,tensile,joystick)
        else:
            self.thrd = SubThread(field,vision,tensile,None)
        self.thrd.statusSignal.connect(self.updateSubThreadStatus)
        self.thrd.finished.connect(self.finishSubThreadProcess)

    # updating GUI according to the status of the subthread
    @pyqtSlot(str)
    def updateSubThreadStatus(self, receivedStr):
        print('Received message from subthread: ',receivedStr)
        # show something on GUI

    # run when the subthread is terminated
    @pyqtSlot()
    def finishSubThreadProcess(self):
        print('Subthread is terminated.')

        vision.clearDrawingRouting()
        self.clearField()
        # disable some buttons etc.

    #=====================================================
    # Real time plot
    # This is showing requested flux density that is stored in
    # field.bxSetpoint, field.bySetpoint, field.bzSetpoint
    # Note: the figure is updating at the speed of self.updateRate defined in
    # __init__.
    #=====================================================
    def setupRealTimePlot(self):
        self.realTimePlot = CustomFigCanvas([-20, 20],'field xyz')
         # put the preview window in the layout
        self.LAYOUT_A.addWidget(self.realTimePlot, *(0,0))
         # connect qt signal to zoom funcion
        self.btn_zoom.clicked.connect(self.realTimePlot.zoom)

    def updatePlot(self):
        # Update the measured coil currents and estimated field values
        field.getXYZ()
        # Update the values on the plot
        self.realTimePlot.addDataX(field.bxEstimate)
        self.realTimePlot.addDataY(field.byEstimate)
        self.realTimePlot.addDataZ(field.bzEstimate)
        # Filter the monitor values for easier viewing
        self.ix1Buf[0] = field.ix1
        self.ix1Buf = np.roll(self.ix1Buf, 1)
        self.ix2Buf[0] = field.ix2
        self.ix2Buf = np.roll(self.ix2Buf, 1)
        self.iy1Buf[0] = field.iy1
        self.iy1Buf = np.roll(self.iy1Buf, 1)
        self.iy2Buf[0] = field.iy2
        self.iy2Buf = np.roll(self.iy2Buf, 1)
        self.iz1Buf[0] = field.iz1
        self.iz1Buf = np.roll(self.iz1Buf, 1)
        self.iz2Buf[0] = field.iz2
        self.iz2Buf = np.roll(self.iz2Buf, 1)
        self.bxEstBuf[0] = field.bxEstimate
        self.bxEstBuf = np.roll(self.bxEstBuf, 1)
        self.byEstBuf[0] = field.byEstimate
        self.byEstBuf = np.roll(self.byEstBuf, 1)
        self.bzEstBuf[0] = field.bzEstimate
        self.bzEstBuf = np.roll(self.bzEstBuf, 1)
        # Update the monitor values for the currents and fields
        self.label_x1.setText('{0:0.1f}'.format(np.mean(self.ix1Buf)))
        self.label_x2.setText('{0:0.1f}'.format(np.mean(self.ix2Buf)))
        self.label_xBreq.setText('{0:0.1f}'.format(field.bxSetpoint))
        self.label_xBact.setText('{0:0.1f}'.format(np.mean(self.bxEstBuf)))
        self.label_y1.setText('{0:0.1f}'.format(np.mean(self.iy1Buf)))
        self.label_y2.setText('{0:0.1f}'.format(np.mean(self.iy2Buf)))
        self.label_yBreq.setText('{0:0.1f}'.format(field.bySetpoint))
        self.label_yBact.setText('{0:0.1f}'.format(np.mean(self.byEstBuf)))
        self.label_z1.setText('{0:0.1f}'.format(np.mean(self.iz1Buf)))
        self.label_z2.setText('{0:0.1f}'.format(np.mean(self.iz2Buf)))
        self.label_zBreq.setText('{0:0.1f}'.format(field.bzSetpoint))
        self.label_zBact.setText('{0:0.1f}'.format(np.mean(self.bzEstBuf)))
        
        self.label_FPS.setText('{0:0.1f}'.format(vision.averageFPS)) #update FPS reading
    
    def setupRealTimePlot2(self):
        self.realTimePlot2 = CustomFigCanvas([-3, 0],'force [N]')
        # put the preview window in the layout
        self.LAYOUT_B.addWidget(self.realTimePlot2,*(0,0))
        # initialize the list to store force values
        self.force_values = []
        self.start_time = time.time() # get the start time
    
    def updatePlot2(self):
        # update the GUI values for the force reading if the tensile thread is running
        if self.chb_startStopSubthread.isChecked():
            # update the force values on the plot
            self.realTimePlot2.addDataX(tensile.load_force_reading())
            self.realTimePlot2.addDataY(0) # filler value
            self.realTimePlot2.addDataZ(0) # filler value
            self.label_loadcell.setText('{0:0.2f}'.format(tensile.load_force_reading())+ ' N')
            # store the force values and distance (mm) as the plot updates
            self.force_values.append([self.thrd.distance, tensile.load_force_reading()])
        else: # if the startstop button is not pressed, force label is stopped to prevent program from lagging
            self.label_loadcell.setText('stopped')
        
        
    #=====================================================
    # Callback Functions
    #=====================================================
    # General control tab
    def setFieldXYZ(self):
        field.setX(self.dsb_x.value())
        field.setY(self.dsb_y.value())
        field.setZ(self.dsb_z.value())

    def clearField(self):
        self.dsb_x.setValue(0)
        self.dsb_y.setValue(0)
        self.dsb_z.setValue(0)
        self.dsb_xGradient.setValue(0)
        self.dsb_yGradient.setValue(0)
        self.dsb_zGradient.setValue(0)
        field.setXYZ(0,0,0)

    def setFieldXYZGradient(self):
        field.setXGradient(self.dsb_xGradient.value())
        field.setYGradient(self.dsb_yGradient.value())
        field.setZGradient(self.dsb_zGradient.value())

    # vision tab
    def on_chb_bypassFilters(self,state):
        vision.setStateFiltersBypassed(state)

    def on_btn_refreshFilterRouting(self):
        vision.createFilterRouting(
            self.editor_vision.toPlainText().splitlines()
            )

    def on_btn_snapshot(self):
        vision.setStateSnapshotEnabled(True)

    def on_chb_objectDetection(self,state):
        algorithm = self.cbb_objectDetectionAlgorithm.currentText()
        vision.setStateObjectDetection(state,algorithm)
        self.cbb_objectDetectionAlgorithm.setEnabled(not state)
      
    def on_setBrightness(self,state):
        vision.setBrightness(state)  
        
    def on_screenWidth(self,state):
        vision.setScreenWidth(state) 

    def on_setResolution(self):
        resolution = self.cbb_resolution.currentText()
        vision.setResolution(resolution)
        time.sleep(0.5)
        
    def on_btn_startVideo(self,state):
        if state and not vision._isUpdating: #start new vision thread here:
            self.on_setResolution() #set the resolution
            self.vis_process_thread = Vis_Process_Thread(vision)
            self.vis_process_thread.start()  
            #self.cbb_subThread.setEnabled(False)
            #self.thrd.start()
            print('Vision started')
        else:
            self.btn_startVideo.setChecked(True)
            #self.cbb_subThread.setEnabled(True)
            #self.vis_process_thread.stop()  
            print('Vision cannot be stopped, and resolution cannot be changed after the vision is started. If you need to chnage the resolution, you must restart the program and set the resolution prior to starting the vision.')


    # subthread
    def on_cbb_subThread(self,subThreadName):
        # an array that stores the name for params. Return param0, param1, ...
        # if not defined.
        labelNames = self.thrd.labelOnGui.get(
            subThreadName,self.thrd.labelOnGui['default']
            )
        minVals = self.thrd.minOnGui.get(
            subThreadName,self.thrd.minOnGui['default']
            )
        maxVals = self.thrd.maxOnGui.get(
            subThreadName,self.thrd.maxOnGui['default']
            )
        defaultVals = self.thrd.defaultValOnGui.get(
            subThreadName,self.thrd.defaultValOnGui['default']
            )
        for i in range(5):
            targetLabel = 'lbl_subThreadParam' + str(i)
            targetSpinbox = 'dsb_subThreadParam' + str(i)
            getattr(self,targetLabel).setText(labelNames[i])
            getattr(self,targetSpinbox).setMinimum(minVals[i])
            getattr(self,targetSpinbox).setMaximum(maxVals[i])
            getattr(self,targetSpinbox).setValue(defaultVals[i])


    def on_chb_startStopSubthread(self,state):
        subThreadName = self.cbb_subThread.currentText()
        if state:
            self.cbb_subThread.setEnabled(False)
            self.thrd.setup(subThreadName)
            self.thrd.start()
            print('Subthread "{}" starts.'.format(subThreadName))
            
            if subThreadName == 'tensileTest':
                print('running tensile test')
                self.setupRealTimePlot2() # only start the tensile plot when the start button is pressed so startup is faster
                
        else:
            self.cbb_subThread.setEnabled(True)
            self.thrd.stop()

    def initDataBuffers(self):
        bufLength = 15
        self.ix1Buf = np.zeros(bufLength)
        self.ix2Buf = np.zeros(bufLength)
        self.iy1Buf = np.zeros(bufLength)
        self.iy2Buf = np.zeros(bufLength)
        self.iz1Buf = np.zeros(bufLength)
        self.iz2Buf = np.zeros(bufLength)
        self.bxEstBuf = np.zeros(bufLength)
        self.byEstBuf = np.zeros(bufLength)
        self.bzEstBuf = np.zeros(bufLength)

    # tensile tab
    def move_left(self): # adjusting tensile gripper position
        tensile.motor_change_dir(0)
        tensile.motor_step()
        
    def move_right(self): # adjusting tensile gripper position
        tensile.motor_change_dir(1)
        tensile.motor_step()
    
    def on_export(self): # exporting force data into a csv        
        # File dialog popup 
        popup = QFileDialog.getSaveFileName(parent = self, caption = 'Select file',
                                               directory = 'tensile.csv', initialFilter = 'CSV file (*.csv)')
        # write time and force data into the file
        filepath = popup[0] # get the saved filepath directory
        with open(filepath,'w+') as fp:
            for j in range(len(self.force_values)):
                fp.write(str(self.force_values[j][0]) + ',' + str(self.force_values[j][1]) + '\n')