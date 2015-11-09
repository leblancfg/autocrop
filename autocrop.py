import cv2
import time
import shutil
import glob
import numpy as np
from contextlib import contextmanager
import os
import math

# Define directory change within context
@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)

# Link the CV goods
cascPath = "haarcascade_frontalface_default.xml"

# Number of error files in batch --errors
n = 0
spent = 1

# ====== Switchbox for external variables ======
fheight = 500 # Height in px of final image
fwidth = 500 # Width in px of final image
fixexp = True # Flag to fix underexposition by CLAHE

# Create the haar cascade
faceCascade = cv2.CascadeClassifier(cascPath)

with cd("~/autocrop/photos/"):

    types = ('*.JPG', '*.jpg') # the tuple of file types
    files_grabbed = []

    for files in types:
        files_grabbed.extend(glob.glob(files))

    # Start timer
    t0 = time.clock()

    # START ITERATION
    for file in files_grabbed:

        # Read the image
        image = cv2.imread(file)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Scale the image
        height, width = (image.shape[:2])
        minface = int(math.sqrt(height*height + width*width) / 8)

        # ====== Detect faces in the image ======
        faces = [[]] # make faces a list of lists
        faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(minface, minface),
        flags = cv2.cv.CV_HAAR_FIND_BIGGEST_OBJECT | cv2.cv.CV_HAAR_DO_ROUGH_SEARCH
        )

        if len(faces) == 0: # Handle no faces
            print " No faces can be detected in file {0}.".format(str(file))
            n = n+1
            break

        # Copy to /bkp
        shutil.copy(file, "bkp")

        # Make padding from probable biggest face
        x, y, w, h = faces[-1]
        pad = h/6 # <- arbitrary number that seems to work well

        # Make sure padding is contained within picture
        while True: # decreases pad by 6% increments to fit crop into image. This could lead to very small faces.
            if y-2*pad < 0 or y+h+pad > height or int(x-1.5*pad) < 0 or x+w+int(1.5*pad) > width:
                pad = 0.94 * pad
            else:
                break

        # Crop the image from the original
        image = image[y-2*pad:y+h+pad, x-1.5*pad:x+w+1.5*pad] # The actual cropping

        # Resize the damn thing
        image = cv2.resize(image, (fheight, fwidth), interpolation = cv2.INTER_AREA)

        # ====== Dealing with underexposition ======
        if fixexp == True: # see line 29

            # Check if under-exposed
            uexp = cv2.calcHist([gray],[0],None,[256],[0,256])

            if sum(uexp[-26:]) < 0.01*sum(uexp) :
                print " Crop for {0} was underexposed".format(str(file))
                # CLAHE
                ycr = cv2.cvtColor(image, cv2.COLOR_BGR2YCR_CB) # change the color image from BGR to YCrCb format
                y,cr,cb = cv2.split(ycr) # split the image into channels
                clahe = cv2.createCLAHE(clipLimit=0.001, tileGridSize=(16,16))
                y = clahe.apply(y)
                image = cv2.merge([y,cr,cb]) # merge 3 channels including the modified 1st channel into one image
                image = cv2.cvtColor(image, cv2.COLOR_YCR_CB2BGR) # change the color image from YCrCb to BGR format

        # Write cropfile
        cropfilename = "{0}".format(str(file))
        cv2.imwrite(cropfilename, image)

        # Move files to /crop
        shutil.move(cropfilename, "crop")


# Stop and print timer
spent = time.clock() - t0
if spent == 0:
    print " No files were cropped"

else:
    print " {0} files have been cropped in {1} ms, average {2} ms/jpg.".format(len(files_grabbed)-n,int(round(1000*spent)), int((1000*spent)/(len(files_grabbed)-n)))
