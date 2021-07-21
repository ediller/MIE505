"""
=============================================================================
vision.py
-----------------------------------------
=============================================================================
"""

import cv2, sys, re, time
from time import sleep
#import numpy as np #just for image tests
#from pydc1394 import Camera #when using firewire camera
from picamera.array import PiRGBArray # Generates a 3D RGB array
from picamera import PiCamera, Color # Provides a Python interface for the RPi Camera Module
import filterlib
import drawing
import objectDetection
from objectDetection import Agent
from datetime import datetime

#==============================================================================
# Mouse callback Functions
#==============================================================================
def showClickedCoordinate(event,x,y,flags,param):
    # global mouseX,mouseY
    if event == cv2.EVENT_LBUTTONDOWN:
        # mouseX,mouseY = x,y
        print('Clicked position  x: {} y: {}'.format(x,y))

class Vision(object):
    def __init__(self, resolution= (640,480), framerate=60, exposure_mode='sports'): #    (320,240)(480,320)(640,480)(1024,768), (2028,1520)
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
        self.snapIndex = 0 #index for image saving

        # instances of Agent class. You can define an array if you have
        # multiple agents.
        # Pass them to *processObjectDetection()*
        self.agent1 = Agent()
        #self.agent2 = Agent()

        # drawings
        # data structure: {"drawingName", "args"}, defined in Subthread
        self.drawingRouting = []
        
        self.screenWidth = 1000 #width of screen in mm. Initialize to a large number

        # video writing
        self._isVideoWritingEnabled = False
        self.videoWriter =  None
        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.stopped = False #should the frame reading process be stopped? Same function as isupdating?
        
        self.cam = PiCamera() #initialize the camera
        self.cam.rotation=180 #rotate the camera view, degrees. 
        self.cam.resolution = resolution #max 2592×1944 . Min 64x64
        self.cam.framerate = framerate
        self.cam.annotate_text_size = 12 # (values 6 to 160, default is 32)
        #self.cam.annotate_background = Color('white')
        self.cam.annotate_foreground = Color('black')
        #self.cam.image_effect=  'blur'
        # allow the camera to warmup
        sleep(0.01)
        self.rawCapture = PiRGBArray(self.cam, self.cam.resolution)
        self.stream = self.cam.capture_continuous(self.rawCapture, format="bgr", use_video_port=True) #format="bgr" for colour
        
        self.averageFPS = 0         #use for FPS calculation
        self.frameReady = False #flag to indicate if a new frame has been grabbed by infiniteFrame thread
              
        cv2.namedWindow(self.windowName(),cv2.WINDOW_AUTOSIZE) #create the window to show images
        cv2.resizeWindow(self.windowName(), 640, 480) #regardless of the true resolution, we'll display at this resolution
        cv2.moveWindow(self.windowName(), 800,30); #move the image display window
        cv2.setMouseCallback(self.windowName(),showClickedCoordinate)
        

    def updateFrame(self): #We use infiniteFrame in its own thread to update images, and just use this updateFrame to show the images in the main GUI thread
        try:
            cv2.imshow(self.windowName(), cv2.resize(self.frameProcessed,(640,480)) ) #show test image
        except AttributeError:
            pass
        #print('completed imshow in updateframe')
        cv2.waitKey(1)
        
           
    def infiniteFrameProcess(self): #this runs in its own thread. Acquire images and perform filtering/detection
        currentTime =  datetime.now() #use for FPS calculation
        pastTime =  datetime.now() #use for FPS calculation
        
        for f in self.stream:
            currentTime =  datetime.now() #get current time
            if currentTime.microsecond*0.0001 > 9:
                self.cam.annotate_text = "%s%i" % (currentTime.strftime("%d/%m/%Y %H:%M:%S.") , currentTime.microsecond*0.0001 )  #write timestamp to camera
            else:
                self.cam.annotate_text = "%s%i%i" % (currentTime.strftime("%d/%m/%Y %H:%M:%S.") ,0, currentTime.microsecond*0.0001 )  #write timestamp to camera
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frameOriginal = f.array
            self.rawCapture.truncate(0) #prepare to receive the next frame
            
            #calculate FPS:
            currentTime =  datetime.now() #get current time
            dTime = currentTime-pastTime #change in time
            dTimeSeconds = dTime.seconds + dTime.microseconds*0.000001
            FPS_now = 1/dTimeSeconds
            self.averageFPS = (FPS_now + 7*self.averageFPS) /8 #crude rolling average of FPS . Displayed to GUI
            #print('FPS infiniteFrameProcess is',"{:.1f}".format(self.averageFPS) ,'. Time since last frame = ',"{:.3f}".format(dTimeSeconds),'s' )  #write timestamp to camera
            pastTime = currentTime
                    
            if not self.isFilterBypassed() or self.isObjectDetectionEnabled(): #image processing only on greyscale image
                self.frameOriginal= cv2.cvtColor(self.frameOriginal, cv2.COLOR_BGR2GRAY) # Grey filter
            ## add filter etc here:
            if not self.isFilterBypassed() and not self.filterRouting == []:
                self.frameFiltered = self.processFilters(self.frameOriginal.copy())
            else:
                self.frameFiltered = self.frameOriginal
                #print('frameFiltered = frameOriginal')
            if self.isObjectDetectionEnabled():
                self.frameProcessed = self.processObjectDetection(
                    self.frameFiltered, self.frameOriginal
                    )
            else:
                self.frameProcessed = self.frameFiltered
            if self.isDrawingEnabled():
                self.frameProcessed = self.processDrawings(self.frameProcessed)
            self.frameProcessed = self.drawScaleBar(self.frameProcessed) 
            if self.isSnapshotEnabled():
                snapName = "%s%i%s" % ('/home/pi/Documents/snapshots/snapshot', self.snapIndex, '.png')
                self.snapIndex = self.snapIndex + 1
                cv2.imwrite(snapName,filterlib.color(self.frameProcessed))
                self.setStateSnapshotEnabled(False)
            #print('exiting infiniteFrameProcess')
            
            if self.stopped:
                self.closeCamera
                return
       

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
        
    def setBrightness(self,state):
        self.cam.brightness = int(state)
        
    def setResolution(self,state):
        resolution = state.split("x")
        resolution = (  int(resolution[0]), int(resolution[1])  )
        print('Setting resolution to ',resolution)        
        self.cam.resolution = resolution
        self.rawCapture = PiRGBArray(self.cam, self.cam.resolution)
        self.stream = self.cam.capture_continuous(self.rawCapture, format="bgr", use_video_port=True) #format="bgr" for colour
        
    def setScreenWidth(self,state):
        self.screenWidth = state #screen width in mm

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

    def drawScaleBar(self, image):
        if self.screenWidth ==1000: return image
        scaleBarWidth = int(1.0*self.cam.resolution[0] / self.screenWidth)
        print('scaleBarWidth width is',scaleBarWidth)
        cv2.line(image, (15,5), (15+scaleBarWidth,5), (255, 0, 0), 1)
        cv2.putText(image,'1 cm', (15,28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 0, 0), 1 )
        return image
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
