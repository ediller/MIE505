"""
=============================================================================
vision.py
-----------------------------------------
=============================================================================
"""

import cv2, sys, re, time
from time import sleep
#from pydc1394 import Camera #when using firewire camera
from picamera.array import PiRGBArray # Generates a 3D RGB array
from picamera import PiCamera # Provides a Python interface for the RPi Camera Module
import filterlib
import drawing
import objectDetection
from objectDetection import Agent

#==============================================================================
# Mouse callback Functions
#==============================================================================
def showClickedCoordinate(event,x,y,flags,param):
    # global mouseX,mouseY
    if event == cv2.EVENT_LBUTTONDOWN:
        # mouseX,mouseY = x,y
        print('Clicked position  x: {} y: {}'.format(x,y))

class Vision(object):
    def __init__(self, resolution=(640,480), framerate=30):
        #self._id = index
        #self._type = type
        #self._guid = guid
        self._isUpdating = False
        self._isFilterBypassed = True
        self._isObjectDetectionEnabled = False
        self._isSnapshotEnabled = False
        self._detectionAlgorithm = ''
         # data structure: {"filterName", "args"}, defined in the GUI
         # text editor
        self.filterRouting = []

        # instances of Agent class. You can define an array if you have
        # multiple agents.
        # Pass them to *processObjectDetection()*
        self.agent1 = Agent()
        #self.agent2 = Agent()

        # drawings
        # data structure: {"drawingName", "args"}, defined in Subthread
        self.drawingRouting = []

        # video writing
        self._isVideoWritingEnabled = False
        self.videoWriter =  None
        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.stopped = False #should the frame reading process be stopped? Same function as isupdating?
        
        self.cam = PiCamera() #initialize the camera
        self.cam.rotation=0 #rotate the camera view, degrees. 
        self.cam.resolution = resolution #max 2592×1944 . Min 64x64
        self.cam.framerate = framerate
        #self.rawCapture = PiRGBArray(self.cam, self.cam.resolution)
        self.rawCapture = PiRGBArray(self.cam)
        #print('PiRGBArray done')
        # allow the camera to warmup
        sleep(0.1)
        # set up the stream
        self.cam.capture(self.rawCapture, format="bgr")
        #print('capture done')
        #self.stream = self.cam.capture_continuous(self.rawCapture, format="bgr", use_video_port=True)
        #image = frames.array
        image = self.rawCapture.array
        #print('image= done')
        
        cv2.namedWindow(self.windowName(),16) # cv2.GUI_NORMAL = 16
        cv2.moveWindow(self.windowName(), 900,100); #move the image display window
        cv2.setMouseCallback(self.windowName(),showClickedCoordinate)
        #print('window setup done')
        
        #self.rawCapture.truncate(0)
        #cv2.imshow(self.windowName(), self.frame) #show test image
        #cv2.waitKey(0)
        cv2.imshow(self.windowName(), image) #show test image
        #print('imshow done')
        cv2.waitKey(1)
        #print('end of init')

        
    def updateFrame(self):
        #print('updateframe')
        #self.rawCapture = PiRGBArray(self.cam)
        self.rawCapture.truncate(0)
        self.cam.capture(self.rawCapture, format="bgr")
        image = self.rawCapture.array
        cv2.imshow(self.windowName(), image) #show test image
        cv2.waitKey(1)
        #cv2.waitKey(0) #wait to confirm that the test image was taken
        #cam.capture(rawCapture, format="bgr")
        #self.rawCapture = PiRGBArray(self.cam)
        # self.cam.capture(self.rawCapture, format="bgr")
        # image = self.rawCapture.array
        # self.rawCapture.truncate(0)
        # #print('updateframe2')
        # #cv2.waitKey(0) #wait to confirm that the test image was taken
        # cv2.imshow(self.windowName(), image)
        #print('updateframe3')
        # for f in self.stream: #show one frame here as a test
            # # grab the frame from the stream and clear the stream in
			# # preparation for the next frame
            # self.frame = f.array
            # self.rawCapture.truncate(0)
            # cv2.imshow(self.windowName(), self.frame) #show test image
            # break
        
        #cv2.waitKey(1) #wait to confirm that the test image was taken
        #print('updateframe done')
        
        # if self.isUpdating():
            # #frameOriginal = self.cam.dequeue() #old
            # # grab the frame from the stream and clear the stream in
            # # preparation for the next frame:
            # print('entering updateFrame in vision.py')
            # frameOriginal = f.array
            # self.rawCapture.truncate(0)
            # if not self.isFilterBypassed() and not self.filterRouting == []:
                # frameFiltered = self.processFilters(frameOriginal.copy())
            # else:
                # frameFiltered = frameOriginal
            # if self.isObjectDetectionEnabled():
                # frameProcessed = self.processObjectDetection(
                    # frameFiltered, frameOriginal
                    # )
            # else:
                # frameProcessed = frameFiltered
            # if self.isDrawingEnabled():
                # frameProcessed = self.processDrawings(frameProcessed)
            # if self.isSnapshotEnabled():
                # cv2.imwrite('snapshot.png',filterlib.color(frameProcessed))
                # self.setStateSnapshotEnabled(False)
            # if self.isVideoWritingEnabled():
                # self.videoWriter.write(filterlib.color(frameProcessed))
            # cv2.imshow(self.windowName(),frameProcessed)
            # frameOriginal.enqueue()


    def closeCamera(self):
        if not self.videoWriter == None:
            self.videoWriter.release()
            self.videoWriter = None
        #self.stream.close()
        self.rawCapture.close()
        self.cam.close()
        cv2.destroyWindow(self.windowName())

    #==========================================================================
    # obtain instance attributes
    #==========================================================================
    def windowName(self):
        return 'Vision Click to print coordinate'

    def isFireWire(self):
        return self._type.lower() == 'firewire'

    def isUpdating(self):
        return self._isUpdating

    def isFilterBypassed(self):
        return self._isFilterBypassed

    def isObjectDetectionEnabled(self):
        return self._isObjectDetectionEnabled

    def isDrawingEnabled(self):
        return not self.drawingRouting == []

    def isSnapshotEnabled(self):
        return self._isSnapshotEnabled

    def isVideoWritingEnabled(self):
        return self._isVideoWritingEnabled

    #==========================================================================
    # set instance attributes
    #==========================================================================
    def setStateUpdate(self,state):
        self._isUpdating = state

    def setStateFiltersBypassed(self,state):
        self._isFilterBypassed = state

    def setStateObjectDetection(self,state,algorithm):
        self._isObjectDetectionEnabled = state
        self._detectionAlgorithm = algorithm

    def setVideoWritingEnabled(self,state):
        self._isVideoWritingEnabled = state

    def setStateSnapshotEnabled(self,state):
        self._isSnapshotEnabled = state

    #==========================================================================
    # Video recording
    #==========================================================================
    def createVideoWriter(self,fileName):
        self.videoWriter = cv2.VideoWriter(
            fileName, fourcc=cv2.VideoWriter_fourcc(*'XVID'), fps=30.0,
            frameSize=(640,480), isColor=True
            )

    def startRecording(self,fileName):
        #self.createVideoWriter(fileName) #disabled by Eric
        #self.setVideoWritingEnabled(True) #disabled by Eric
        print('Recording Disabled in vision.py by Eric: Start recording' + fileName)

    def stopRecording(self):
        #self.setStateSnapshotEnabled(False)
        #self.videoWriter.release()
        print('Stop recording.')

    #==========================================================================
    # <Filters>
    # Define the filters in filterlib.py
    #==========================================================================
    def createFilterRouting(self,text):
        self.filterRouting = []
        for line in text:
            line = line.split('//')[0]  # strip after //
            line = line.strip()         # strip spaces at both ends
            match = re.match(r"(?P<function>[a-z0-9_]+)\((?P<args>.*)\)", line)
            if match:
                name = match.group('function')
                args = match.group('args')
                args = re.sub(r'\s+', '', args) # strip spaces in args
                self.filterRouting.append({'filterName': name, 'args': args})

    def processFilters(self,image):
        for item in self.filterRouting:
            image = getattr(
                filterlib,item['filterName'],filterlib.filterNotDefined
                )(image,item['args'])
        # You can add custom filters here if you don't want to use the editor
        return image

    #==========================================================================
    # <object detection>
    # Object detection algorithm is executed after all the filters
    # It is assumed that "imageFiltered" is used for detection purpose only;
    # the boundary of the detected object will be drawn on "imageOriginal".
    # information of detected objects can be stored in an instance of "Agent"
    # class.
    #==========================================================================
    def processObjectDetection(self,imageFiltered,imageOriginal):
        # convert to rgb so that coloured lines can be drawn on top
        imageOriginal = filterlib.color(imageOriginal)

        # object detection algorithm starts here
        # In this function, information about the agent will be updated, and
        # the original image with the detected objects highlighted will be
        # returned.
        algorithm = getattr(
            objectDetection, self._detectionAlgorithm,
            objectDetection.algorithmNotDefined
            )
        # pass instances of Agent class if you want to update its info
        imageProcessed = algorithm(imageFiltered,imageOriginal,self.agent1)
        return imageProcessed

    #==========================================================================
    # <subthread drawing>
    # Used to draw lines etc. on a plot
    # For showing the path that the robot wants to follow
    #==========================================================================
    def clearDrawingRouting(self):
        self.drawingRouting = []

    def addDrawing(self,name,args=None):
        self.drawingRouting.append({'drawingName': name, 'args': args})

    def processDrawings(self,image):
        # convert to rgb so that coloured lines can be drawn on top
        image = filterlib.color(image)
        for item in self.drawingRouting:
            image = getattr(
                drawing,item['drawingName'],drawing.drawingNotDefined
                )(image,item['args'])
        return image
