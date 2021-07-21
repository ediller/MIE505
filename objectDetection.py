import cv2, math
import numpy as np


def algorithmNotDefined(imageFiltered,imageOriginal,*args):
    """Call this function if the selected algorithm is not defined."""
    print('Algorithm name not defined in objectDetection.py')
    return imageOriginal


def detectBiggestContour(imageFiltered,imageOriginal,agent):
    """Detect the biggest contour (except the edge of the screen).

    Use a binary image as input in this algorithm.
    """
    imageFiltered=cv2.copyMakeBorder(
        imageFiltered, top=1, bottom=1, left=1, right=1,
        borderType= cv2.BORDER_CONSTANT, value=[255,255,255]
        )
    nOfSamples = 2
    contours, hierarchy = cv2.findContours(
        imageFiltered, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
    cnts = sorted(contours, key = cv2.contourArea, reverse = True)[:nOfSamples]
    if len(cnts) > 1:
        targetCnt = cnts[1] # cnt[0] is the edge of the screen
        # get info
        #(x,y),(MA,ma),angle = cv2.fitEllipse(targetCnt) #ERIC commented this out since it was crashing
        #angleCorrected = -angle + 90#ERIC commented this out since it was crashing
        #agent.set(x,y,angleCorrected) # update the position of the agnet#ERIC commented this out since it was crashing
        #print('agent at (x,y)=',x,y,'angle=',angleCorrected*180/3.14,'degrees')#ERIC commented this out since it was crashing
        # draw contour
        rect = cv2.minAreaRect(targetCnt) # (x,y)(w,h)theta
        box = np.int0(cv2.boxPoints(rect)) # vertices of the bounding rect
        # Draw boundingRect on the original image
        cv2.drawContours(imageOriginal,[box],0,(0,255,0), 3)
    return imageOriginal


def drawAxis(img, start_pt, vec, colour, length):
    """Detect all contours and use PCA to find the orientation.

    Use a binary image as input in this algorithm. PCA is primary component
    analysis.
    """
    CV_AA = 16 # antialias
    end_pt = (int(start_pt[0] + length * vec[0]),
            int(start_pt[1] + length * vec[1]))
    cv2.circle(img, (int(start_pt[0]), int(start_pt[1])), 5, colour, 2)
    cv2.line(
        img, (int(start_pt[0]), int(start_pt[1])), end_pt, colour, 2, CV_AA
        );
    angle = math.atan2(vec[1], vec[0])

    qx0 = int(end_pt[0] - 9 * math.cos(angle + math.pi / 4));
    qy0 = int(end_pt[1] - 9 * math.sin(angle + math.pi / 4));
    cv2.line(img, end_pt, (qx0, qy0), colour, 1, CV_AA);

    qx1 = int(end_pt[0] - 9 * math.cos(angle - math.pi / 4));
    qy1 = int(end_pt[1] - 9 * math.sin(angle - math.pi / 4));
    cv2.line(img, end_pt, (qx1, qy1), colour, 1, CV_AA);


def primaryComponentAnalysis(imageFiltered,imageOriginal,agent):
    """Use primary component analysis to detect the agent's orientation."""
    #   cv2.CHAIN_APPROX_NONE       save all points
    #   cv2.CHAIN_APPROX_SIMPLE     only save key points
    contours, hierarchy = cv2.findContours(  #ORIGINAL WAS img, contours, hierarchy = cv2.findContours(
        imageFiltered, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )
    #print(len(contours), 'contours found.')
    nOfSamples = 2
    cnts = sorted(contours, key = cv2.contourArea, reverse = True)[:nOfSamples]
    if len(cnts) > 1:
        targetCnt = cnts[1] # cnt[0] is the edge of the screen
    
    #for i in range(0,len(contours)): #we could change this line to only detect the main contour I think using range(1):#
        #print('i=',i)
        area = cv2.contourArea(targetCnt)# calculate contour area
        # Remove small areas (noise) and big areas (the edges of the screen)
#         print('area of contour',i, ' is ',area)
#         if area < 100 or area > 1e4: #this needs to be changed for different image resolutions
#             continue
        cv2.drawContours(
            imageOriginal, cnts, 1, (0, 255, 0), 2, 8, hierarchy, 0
            )
        X = np.array(targetCnt, dtype=np.float).reshape(
            (targetCnt.shape[0], targetCnt.shape[2])
            ) # save contour as float array
        # one-dimensioanl Primary Component Analysis
        mean, eigenvectors = cv2.PCACompute(
            X, mean=np.array([], dtype=np.float), maxComponents=1
            )
        pt = (mean[0][0], mean[0][1])
        vec = (eigenvectors[0][0], eigenvectors[0][1]) # eigen vectors
        drawAxis(imageOriginal, pt, vec, (0, 0, 255), 150)
        angle = math.atan2(-vec[1], vec[0])
        x,y = pt
        agent.set(x,y,angle) # update the position of the agnet
        print('agent at (x,y)=(',int(x),int(y),')px','angle=',int(angle*180/3.14),'degrees')
    return imageOriginal


class Agent():
    def __init__(self):
        self.x = 0
        self.y = 0
        self.orientation = 0

    def set(self,x,y,orientation = 0):
        self.x = x
        self.y = y
        self.orientation = orientation
