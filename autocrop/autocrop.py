# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
from contextlib import contextmanager
import cv2
import glob
import numpy as np
import os
import shutil
import sys

from .__version__ import __title__, __description__, __author__, __version__

fixexp = True  # Flag to fix underexposition
INPUT_FILETYPES = ['*.jpg', '*.jpeg', '*.bmp', '*.dib', '*.jp2',
                   '*.png', '*.webp', '*.pbm', '*.pgm', '*.ppm',
                   '*.sr', '*.ras', '*.tiff', '*.tif']
INCREMENT = 0.06
GAMMA_THRES = 0.001 
GAMMA = 0.90
FACE_RATIO = 6

# Load XML Resource
cascFile= 'haarcascade_frontalface_default.xml'
d = os.path.dirname(sys.modules['autocrop'].__file__)
cascPath = os.path.join(d, cascFile)

# Define directory change within context
@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)

# Define simple gamma correction fn
def gamma(img, correction):
    img = cv2.pow(img/255.0, correction)
    return np.uint8(img*255)

def crop(image, fwidth=500, fheight=500):
    """Given a ndarray image with a face, returns cropped array.

    Arguments:
        - image, the numpy array of the image to be processed.
        - fwidth, the final width (px) of the cropped img. Default: 500
        - fheight, the final height (px) of the cropped img. Default: 500
    Returns:
        - image, a cropped numpy array

    ndarray, int, int -> ndarray
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Scale the image
    height, width = (image.shape[:2])
    minface = int(np.sqrt(height*height + width*width) / 8)

    # Create the haar cascade
    faceCascade = cv2.CascadeClassifier(cascPath)

    # ====== Detect faces in the image ======
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(minface, minface),
        flags = cv2.CASCADE_FIND_BIGGEST_OBJECT | cv2.CASCADE_DO_ROUGH_SEARCH
    )

    # Handle no faces
    if len(faces) == 0: 
        return None

    # Make padding from probable biggest face
    x, y, w, h = faces[-1]
    pad = h / FACE_RATIO

    # Make sure padding is contained within picture
    while True:  # decreases pad by 6% increments to fit crop into image. Can lead to very small faces.
        if y-2*pad < 0 or y+h+pad > height or int(x-1.5*pad) < 0 or x+w+int(1.5*pad) > width:
            pad = (1 - INCREMENT) * pad
        else:
            break

    # Crop the image from the original
    h1 = int(x-1.5*pad) 
    h2 = int(x+w+1.5*pad)
    v1 = int(y-2*pad)
    v2 = int(y+h+pad)
    image = image[v1:v2, h1:h2]

    # Resize the damn thing
    image = cv2.resize(image, (fheight, fwidth), interpolation = cv2.INTER_AREA)

    # ====== Dealing with underexposition ======
    if fixexp == True:
        # Check if under-exposed
        uexp = cv2.calcHist([gray], [0], None, [256], [0,256])
        if sum(uexp[-26:]) < GAMMA_THRES * sum(uexp) :
            image = gamma(image, GAMMA)
    return image

def main(path, fheight, fwidth):
    """Given path containing image files to process, will
    1) copy them to `path/bkp`, and 
    2) create face-cropped versions and place them in `path/crop`
    """
    errors = 0
    with cd(path):
        files_grabbed = []
        for files in INPUT_FILETYPES:
            files_grabbed.extend(glob.glob(files))

        for file in files_grabbed:
            # Copy to /bkp
            shutil.copy(file, 'bkp')

            # Perform the actual crop
            input  = cv2.imread(file)
            image = crop(input, fwidth, fheight)

            # Make sure there actually was a face in there
            if image == None:
                print(' No faces can be detected in file {0}.'.format(str(file)))
                errors += 1
                continue

            # Write cropfile
            cropfilename = '{0}'.format(str(file))
            cv2.imwrite(cropfilename, image)

            # Move files to /crop
            shutil.move(cropfilename, 'crop')

    # Stop and print timer
    print(' {0} files have been cropped'.format(len(files_grabbed) - errors))

def cli():
    parser = argparse.ArgumentParser(description='Automatically crops faces from batches of pictures')
    parser.add_argument('-p', '--path', default='photos', help='Folder where images to crop are located. Default: photos/')
    parser.add_argument('-w', '--width', type=int, default=500, help='Width of cropped files in px. Default: 500')
    parser.add_argument('-H', '--height', type=int, default=500, help='Height of cropped files in px. Default: 500')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s version {}'.format(__version__))

    args = parser.parse_args()
    print('Processing images in folder:', args.path)

    main(args.path, args.height, args.width)

