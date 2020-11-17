# This code is written at BigVision LLC. It is based on the OpenCV project. It is subject to the license terms in the LICENSE file found in this distribution and at http://opencv.org/license.html

import cv2 as cv
import argparse
import sys
import numpy as np
import os.path
import pytesseract
import os  
import requests
from app import socketio

# Initialize the parameters
confThreshold = 0.5  # Confidence threshold
nmsThreshold = 0.4  # Non-maximum suppression threshold

inpWidth = 416  # 608     # Width of network's input image
inpHeight = 416  # 608     # Height of network's input image
IMAGE_SIZE = 200
# Load names of classes
classesFile = "app/cv/classes.names"

classes = None
with open(classesFile, 'rt') as f:
    classes = f.read().rstrip('\n').split('\n')

# Give the configuration and weight files for the model and load the network using them.

modelConfiguration = "app/cv/darknet-yolov3.cfg"
modelWeights = "app/cv/model.weights"

net = cv.dnn.readNetFromDarknet(modelConfiguration, modelWeights)
net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)

# Get the names of the output layers


def getOutputsNames(net):
    # Get the names of all the layers in the network
    layersNames = net.getLayerNames()
    # Get the names of the output layers, i.e. the layers with unconnected outputs
    return [layersNames[i[0] - 1] for i in net.getUnconnectedOutLayers()]
# Draw the predicted bounding box
def drawPred(classId, conf, left, top, right, bottom,frame):
    # Draw a bounding box.
    #    cv.rectangle(frame, (left, top), (right, bottom), (255, 178, 50), 3)
    cv.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 3)

    label = '%.2f' % conf

    # Get the label for the class name and its confidence
    if classes:
        assert(classId < len(classes))
        label = '%s: %s' % (classes[classId], label)

    # Display the label at the top of the bounding box
    labelSize, baseLine = cv.getTextSize(
        label, cv.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    top = max(top, labelSize[1])
    image = cv.rectangle(frame, (left, top - round(1.5*labelSize[1])), (left + round(1.5*labelSize[0]), top + baseLine), (255, 0, 255), cv.FILLED)
    crop_img = frame[top :bottom, left:right]
    crop_img = cv.cvtColor(crop_img, cv.COLOR_BGR2GRAY)
    cv.imshow("Detected Number Plate", crop_img)
    predicted_result = pytesseract.image_to_string(crop_img, lang ='eng', config ='--oem 3 --psm 6') 
    if predicted_result != "":
        response = requests.post('http://localhost:5000/user', json = {'number_plate':str(predicted_result.strip())})
        if response.status_code == 200 :
            socketio.emit('my_response',{'data': predicted_result, 'count': 1},namespace='/test')
            cv.destroyWindow('Detected Number Plate')
    # making db 
    #cv.rectangle(frame, (left, top - round(1.5*labelSize[1])), (left + round(1.5*labelSize[0]), top + baseLine),    (255, 255, 255), cv.FILLED)
    cv.putText(frame, label, (left, top),cv.FONT_HERSHEY_SIMPLEX, 0.70, (255, 255, 255), 2)

# Remove the bounding boxes with low confidence using non-maxima suppression

def postprocess(frame, outs):
    frameHeight = frame.shape[0]
    frameWidth = frame.shape[1]

    classIds = []
    confidences = []
    boxes = []
    # Scan through all the bounding boxes output from the network and keep only the
    # ones with high confidence scores. Assign the box's class label as the class with the highest score.
    classIds = []
    confidences = []
    boxes = []
    for out in outs:
        # print("out.shape : ", out.shape)
        for detection in out:
            # if detection[4]>0.001:
            scores = detection[5:]
            classId = np.argmax(scores)
            # if scores[classId]>confThreshold:
            confidence = scores[classId]
            if detection[4] > confThreshold:
                print(detection[4], " - ", scores[classId],
                      " - th : ", confThreshold)
                print(detection)
            if confidence > confThreshold:
                center_x = int(detection[0] * frameWidth)
                center_y = int(detection[1] * frameHeight)
                width = int(detection[2] * frameWidth)
                height = int(detection[3] * frameHeight)
                left = int(center_x - width / 2)
                top = int(center_y - height / 2)
                classIds.append(classId)
                confidences.append(float(confidence))
                boxes.append([left, top, width, height])

    # Perform non maximum suppression to eliminate redundant overlapping boxes with
    # lower confidences.
    indices = cv.dnn.NMSBoxes(boxes, confidences, confThreshold, nmsThreshold)
    for i in indices:
        i = i[0]
        box = boxes[i]
        left = box[0]
        top = box[1]
        width = box[2]
        height = box[3]
        drawPred(classIds[i], confidences[i], left,top, left + width, top + height,frame)

def main():
    cap = cv.VideoCapture(0)
    while True:
        # get frame from the video
        hasFrame, frame = cap.read()
        # Stop the program if reached end of video
        if not hasFrame:
            print("Done processing !!!")
            print("Output file is stored as ")
            cv.waitKey(3000)
            break
        # Create a 4D blob from a frame.
        blob = cv.dnn.blobFromImage(frame, 1/255, (inpWidth, inpHeight), [0, 0, 0], 1, crop=False)
        # Sets the input to the network
        net.setInput(blob)
        # Runs the forward pass to get output of the output layers
        outs = net.forward(getOutputsNames(net))
        # Remove the bounding boxes with low confidence
        postprocess(frame, outs)
        # Put efficiency information. The function getPerfProfile returns the overall time for inference(t) and the timings for each of the layers(in layersTimes)
        t, _ = net.getPerfProfile()
        label = 'Inference time: %.2f ms' % (t * 1000.0 / cv.getTickFrequency())
        
        img = cv.resize(frame, (IMAGE_SIZE,IMAGE_SIZE))
        cv.putText(img, label, (0, 15), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))
        cv.imshow("Camera Stream", img)
        k = cv.waitKey(1)
        if k%256 == 27:
            # ESC pressed
            print("Escape hit, closing system ...")
            cap.release()
            cv.destroyAllWindows()
            os._exit(os.EX_OK) 
            break
if __name__ == "__main__":

    main()