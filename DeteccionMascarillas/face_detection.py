from tensorflow.keras.applications.resnet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
import numpy as np
import argparse
import cv2
import os

def detect_and_predict_mask(frame, faceNet, maskNet):
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 1.0, (800, 800), (104.0, 177.0, 123.0))

    faceNet.setInput(blob)
    detections = faceNet.forward()
    faces = []
    locs = []
    preds = []

    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        
        if confidence > args.confidence:			
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            (startX, startY) = (max(0, startX), max(0, startY))
            (endX, endY) = (min(w - 1, endX), min(h - 1, endY))
            
            face = frame[startY:endY, startX:endX]
            face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            face = cv2.resize(face, (224, 224))
            face = img_to_array(face)
            face = preprocess_input(face)

            faces.append(face)
            locs.append((startX, startY, endX, endY))

    if len(faces) > 0:		
        faces = np.array(faces, dtype="float32")
        preds = maskNet.predict(faces, batch_size=32)

    return (locs, preds)

def process_frame(frame, size, faceNet, maskNet):
    (locs, preds) = detect_and_predict_mask(frame, faceNet, maskNet)

    people_detected = 0
    for (box, pred) in zip(locs, preds):
        (startX, startY, endX, endY) = box
        (mask, withoutMask) = pred

        
        if mask > withoutMask:
            label = "CON mascarilla"
            color = (0, 255, 0)

        else:
            label = "SIN mascarilla"
            color = (0, 0, 255)
        
        people_detected = people_detected + 1
        cv2.putText(frame, label, (startX-50, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)

    cv2.putText(frame, f'Total personas: {people_detected}', (20,30), cv2.FONT_HERSHEY_DUPLEX, 1, (255,0,0), 3)

    # if(not args.picture):
    frame = cv2.resize(frame, frame_size)
#    else: frame = cv2.resize(frame, (1200,720))

    return frame

ap = argparse.ArgumentParser()
ap.add_argument("-f", "--face", type=str,
	default="face_detector",
	help="path to face detector model directory")
ap.add_argument("-m", "--mask", type=str,
	default="mask_detector/advanced_model_detector_v2.model",
	help="path to trained face mask detector model")

ap.add_argument("-v", "--video", 
    action='store_true',
	help="path to video")
ap.add_argument("-c", "--camera", 
    action='store_true',
	help="indicates if a camera is going to be used")
ap.add_argument("-p", "--picture", 
    action='store_true',
	help="path to picture")

ap.add_argument("-i", "--input", type=str,
	help="path to video")
ap.add_argument("-o", "--output", type=str,
	required=True,
	help="output file video")

ap.add_argument("-C", "--confidence", type=float, default=0.5,
	help="minimum probability to filter weak detections")

args = ap.parse_args()

if ((args.picture or args.video) and args.camera):
    ap.error("-v/--video -c/--camera -p/--picture are mutually exclusive")

if (args.picture and args.video):
    ap.error("-v/--video and -p/--picture are mutually exclusive")

if (not (args.video or args.picture) and args.input):
    ap.error("Given an input it is mandatory to select -v/--video and -p/--picture")

if ((args.video or args.picture) and args.input is None):
    ap.error("It is mandatory to give an input file with -v/--video and -p/--picture")


print("[INFO] loading face detector model...")
prototxtPath = os.path.sep.join([args.face, "deploy.prototxt"])
weightsPath = os.path.sep.join([args.face, "res10_300x300_ssd_iter_140000.caffemodel"])
faceNet = cv2.dnn.readNet(prototxtPath, weightsPath)

print("[INFO] loading face mask detector model...")
maskNet = load_model(args.mask)

frame_size = (560,400)

if(args.video or args.camera):
    print("[INFO] loading video stream...")

    if(args.video):
        in_video = cv2.VideoCapture(args.input)
    else: in_video = cv2.VideoCapture(0)
    
    if not in_video.isOpened(): print("Error opening video stream")
    else: print("[INFO] video stream loaded successfully...")

    out_video = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*'mp4v'), 20.0, frame_size)
    
    while True:
        ret, frame = in_video.read()
        if ret: 
            frame = process_frame(frame,frame_size,faceNet,maskNet)
            out_video.write(frame)
            cv2.imshow("People counter and face mask detector", frame)
        else:
            break
        
        if (cv2.waitKey(1) & 0xFF) == ord("q"):
            break

    cv2.destroyAllWindows()
    out_video.release()
    in_video.release()

if(args.picture):
    print("[INFO] loading picture...")
    frame = cv2.imread(args.input)

    frame = process_frame(frame, frame_size, faceNet, maskNet)
    cv2.imwrite(args.output, frame)
    cv2.imshow("People counter and face mask detector", frame)
    
    if (cv2.waitKey(0) & 0xFF) == ord("q"): exit

