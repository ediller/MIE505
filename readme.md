# MIE505 CoilSystemPython

A Python3-based program for the coil system. Ported from C code. This code was originally developed for our research lab, and adapted in summer 2021 by Eric Diller, Cameron Forbrigger and Priscilla Lai for use with new coil systems for MIE505 Practicals.

## Features
* Runs on Raspberry Pi 4B. (Should also run on earlier Pi's)
* Control the electromagnetic coils via motor driver I/O board.
* Realtime vision feedback from Raspberry Pi cameras.
* Filtering and pre-processing of the images, based on OpenCV.
* Object detection algorithm.
* Qt5-based GUI, which allows easy customization.
* Multithreading module for controlling multiple agents according to the feedback data from the cameras.
* Preview window (up to 60 Hz) for the X, Y, and Z magnetic field.
* Controlling the magnetic field with a Joystick controller. (optional, not yet ported fully)
            
Contents
--------------------

<!-- TOC orderedList:true -->


1. [Usage](#usage)
    1. [Installation](#installation)
    2. [How to run](#how-to-run)
    3. [Utilities](#utilities)
2. [Structure](#structure)
3. [Vision](#vision)
    1. [Camera](#camera)
    2. [Filters](#filters)
    3. [Object Detection](#object-detection)
4. [New Features](#new-features)


5. [Known Issues](#known-issues)

<!-- /TOC -->


## Usage

### Installation


```
The best installation process is to completely copy the SD card from the Raspberry Pi to a new flash card. Use the SD Card Copier utility on the Raspberry Pi, with the USB-SD reader adapter.
Follow instructions in Eric's Install instructions if the system needs to be installed on a new Pi. 
```

### How to run

open terminal and cd to the target directory (currently /Documents/MIE505/CoilSystemMaster/) and run

```
python3 main.py
```

### Utilities

#### Screen Recording

Not recommended due to CPU limitation on Raspberry Pi. 


## Structure

To have a better understanding of the program, I would recommend you first have a look at "fieldManager.py".

After that, open the GUI and "callbacks.py" to follow the signal flow and event handler (pyqtSlot).

Go through "vision.py" to see how images are processed, and "objectDetection.py" to see how objects are detected and stored in instances of Agent class. A thread is created to run the Vision using "vis_thread.py".

Read "subthread.py" in the end because it uses all the above-mentioned classes to do some complex stuff. E.g. Apply a rotational field with time-varying frequency/magnitude based on the position of the object detected.

```
main.py

callbacks.py
│
└───mathfx.py [some macros for maths] 
└───syntax.py [highlight the keywords in GUI editor_vision]
|
└───fieldManager.py [send commands to GPIO; store XYZ field strength]
│  
│
└───vision.py [capture frames; apply filters; detect objects]
│       │   filterlib.py [define filters]
│       │   objectDetection.py [define object detection algorithms]
|       |   drawing.py [allow users to draw line etc. in a subthread]
│
│
└───subthread.py [run multithreading tasks]
|
└───vis_thread.py [run vision acquisition and processing tasks]
│
└───realTimePlot.py [plot a real-time preview window of the magnetic field]
│
└───OPTIONAL: PS3Controller.py [enable joystick/controllers]

```
## Vision

### Camera



### Filters

Go to filterlib.py and define your filter. E.g. myfilter(param1,param2,...)

Then you can directly use it in the GUI by typing "myfilter(param1, param2,...)"

### Object Detection

![Object Detection](https://github.com/atelier-ritz/CoilSystemPython/blob/master/documentation/object_detection.png)

Go to GUI and add the name of your algorithm in algorithm combobox.

Go to vision.py __init__() function. Add a class attribute of the object to be detected. For example, self.gripper = Agent(), self.cargo = Agent()

Define your algorithm in objectDetection.py. Refer to algorithmA() as an Example.

Go to processObjectDetection() and pass your "agents" (instances of Agent Class) to the algorithm you just created.

The parameters (x, y, and orientation, if applicable) are updated at 60 Hz (defined in setupTimer() in callbacks.py).

These values can be accessed in the subthread.py by using self.vision.<nameOfYourAgent>.x, self.vision.<nameOfYourAgent>.y, and self.vision.<nameOfYourAgent>.orientation.


### Joystick

pygame needs to be installed to use the joystick module. To enable it, uncomment the following lines in callbacks.py.

```
from PS3Controller import DualShock
joystick = DualShock()
```

Although we only tested a PS3 Dualshock controller connected via USB, you should be able to work with any controller. (Try using "lsusb" command and "dmesg" command in the terminal to see if the controller is detected.) 

The available input for a PS3 controllers are 6 axis input and 16 button inputs.

Run the follwing command in the directory to test the controller input.

```
python3 PS3Controller.py
```

Refer to the sample code in *tianqiGripper()* in subThread.py.

### signal-generator

Added oscBetween() function that can be used in "subthread.py".

This function generates an oscillating value between a lowerbound and an upperbound.

The following oscillation waveforms are available: sin, saw, square, triangle.

Please refer to "exampleOscBetween" in "subthread.py" and the "oscBetween()" function defined in "mathfx.py".

### Preview Window

Added a window for real time preview of magnetic fields.

Also added some examples in subthread.py.

![Preview Window](https://github.com/atelier-ritz/CoilSystemPython/blob/master/documentation/previewwindow.gif)

### Drawing

In the old version, users can apply filters to the image, or highlight the object detected.

However, it didn't allow users to draw lines and circles directly on the frames captured.

This is necessary when, for example, users want to draw a vector pointing from the current robot position to the goal position.

Please refer to the "swimmerPathFollowing" example and "drawing" example in subThread.py.

### Recording

To take a snapshot, click the snapshot button in the GUI.

To record a video in a subThread, use the following commands):

```
self.vision.startRecording('YOUR_FILE_NAME.avi')
self.vision.stopRecording()
```

Please refer to the *drawing()* in subThread.py.

## Known Issues

1. The resolution of the imaging can only be changed before starting the vision. If you want to change the resolution, you need to restart the program.

2. The vision is quite slow. You can expect 10-15fps at 640x480, or 20fps at 480x320.
