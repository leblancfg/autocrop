import cv2
import time
import shutil
import glob
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

# Create final height and width variables
fheight = 500
fwidth = 500

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

        # Copy to /bkp
        shutil.copy(file, "bkp")

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

        #print "Found {0} faces!".format(len(faces))
        #print faces[-1][3]

        # Stop this iteration if no face found --errors ============= for now that'll be it;
        # Could fiddle around with scaleFactor, or CLAHE the grayscale and try again.
        if len(faces) == 0:
            print "No faces can be detected in file {0}.".format(str(file))
            n = n+1

        else:

            # Make padding from probable biggest face
            x, y, w, h = faces[-1]
            pad = h/6

            # Make sure padding is contained within picture
            while True: # decreases pad by 5% increments to fit crop into image
                if y-2*pad < 0 or y+h+pad > height or int(x-1.5*pad) < 0 or x+w+int(1.5*pad) > width:
                    pad = 0.95 * pad
                else:
                    break

            # Crop the image from the original
            image = image[y-2*pad:y+h+pad, x-1.5*pad:x+w+1.5*pad] # the actual cropping

            # Resize the damn thing
            image = cv2.resize(image, (fheight, fwidth), interpolation = cv2.INTER_AREA)

            # === CLAHE ===
            ycr = cv2.cvtColor(image, cv2.COLOR_BGR2YCR_CB) #change the color image from BGR to YCrCb format
            y,cr,cb = cv2.split(ycr) # split the image into channels
            clahe = cv2.createCLAHE(clipLimit=0.9, tileGridSize=(16,16))
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
    print " {0} files have been cropped in {1} s, average {2} ms/jpg.".format(len(files_grabbed)-n,int(round(spent)), int((spent)/(len(files_grabbed)-n)))
