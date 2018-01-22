# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
from contextlib import contextmanager
import cv2
from glob import glob
import numpy as np
import os
import shutil
import sys

from .__version__ import __version__

FIXEXP = True  # Flag to fix underexposition
INPUT_FILETYPES = ['*.jpg', '*.jpeg', '*.bmp', '*.dib', '*.jp2',
                   '*.png', '*.webp', '*.pbm', '*.pgm', '*.ppm',
                   '*.sr', '*.ras', '*.tiff', '*.tif']
INCREMENT = 0.06
GAMMA_THRES = 0.001
GAMMA = 0.90
FACE_RATIO = 6
QUESTION_OVERWRITE = "Overwrite image files?"

# Load XML Resource
cascFile = 'haarcascade_frontalface_default.xml'
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
        flags=cv2.CASCADE_FIND_BIGGEST_OBJECT | cv2.CASCADE_DO_ROUGH_SEARCH
    )

    # Handle no faces
    if len(faces) == 0:
        return None

    # Make padding from probable biggest face
    x, y, w, h = faces[-1]
    pad = h / FACE_RATIO

    # Make sure padding is contained within picture
    # decreases pad by 6% increments to fit crop into image.
    # Can lead to very small faces.
    while True:
        if (y-2*pad < 0 or y+h+pad > height or
                int(x-1.5*pad) < 0 or x+w+int(1.5*pad) > width):
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
    image = cv2.resize(image, (fheight, fwidth), interpolation=cv2.INTER_AREA)

    # ====== Dealing with underexposition ======
    if FIXEXP:
        # Check if under-exposed
        uexp = cv2.calcHist([gray], [0], None, [256], [0, 256])
        if sum(uexp[-26:]) < GAMMA_THRES * sum(uexp):
            image = gamma(image, GAMMA)
    return image


def main(input_d, output_d, fheight, fwidth):
    """Crops folder of images to the desired height and width if a face is found

    If input_d == output_d, overwrites all files where face was found.

    Args:
        input_d (str): Directory to crop images from.
        output_d (str): Directory where cropped images are placed.
        fheight (int): Height (px) to which to crop the image.
        fwidth (int): Width (px) to which to crop the image.

    Side Effects:
        Creates image files in output directory.
    """
    errors = 0
    # TODO: Do all work based off absolute paths
    with cd(input_d):
        files_grabbed = []
        for files in INPUT_FILETYPES:
            # Handle e.g. both jpg and JPG
            files_grabbed.extend(glob(files))
            files_grabbed.extend(glob(files.upper()))

        for file in files_grabbed:
            # Copy to /bkp
            shutil.copy(file, 'bkp/')

            # Perform the actual crop
            input = cv2.imread(file)
            image = crop(input, fwidth, fheight)

            # Make sure there actually was a face in there
            if isinstance(image, type(None)):
                print('No faces can be detected in file {}.'.format(str(file)))
                errors += 1
                continue

            # Write cropfile
            cropfilename = '{0}'.format(str(file))
            cv2.imwrite(cropfilename, image)

            # Move files to /crop
            shutil.move(cropfilename, 'crop/')

    # Stop and print timer
    print(' {} files have been cropped'.format(len(files_grabbed) - errors))


def input_path(p):
    """Returns absolute path, only if input is a valid directory"""
    p = os.path.abspath(p)
    if os.path.isdir(p):
        return p
    else:
        raise argparse.ArgumentTypeError('Invalid path name')


def output_path(p):
    """Returns absolute path, if input is a valid directory name.
    If directory doesn't exist, creates it."""
    p = os.path.abspath(p)
    if not os.path.isdir(p):
        os.makedirs(p)
    return p


def size(i):
    """Returns valid only if input is a positive integer under 1e5"""
    try:
        i = int(i)
    except TypeError:
        raise argparse.ArgumentTypeError('Invalid pixel size')

    if i > 0 and i < 1e5:
        return i
    else:
        raise argparse.ArgumentTypeError('Invalid pixel size')


def compat_input(s=''):
    """Compatibility function to permit testing for Python 2 and 3"""
    try:
        return raw_input(s)
    except NameError:
        return input(s)


def confirmation(question, default=True):
    """Ask a yes/no question via standard input and return the answer.

    If invalid input is given, the user will be asked until
    they acutally give valid input.

    Args:
        question(str):
            A question that is presented to the user.
        default(bool|None):
            The default value when enter is pressed with no value.
            When None, there is no default value and the query
            will loop.
    Returns:
        A bool indicating whether user has entered yes or no.

    Side Effects:
        Blocks program execution until valid input(y/n) is given.
    """
    yes_list = ["yes", "y"]
    no_list = ["no", "n"]

    default_dict = {  # default => prompt default string
        None: "[y/n]",
        True: "[Y/n]",
        False: "[y/N]",
    }

    default_str = default_dict[default]
    prompt_str = "%s %s " % (question, default_str)

    while True:
        choice = compat_input(prompt_str).lower()

        if not choice and default is not None:
            return default
        if choice in yes_list:
            return True
        if choice in no_list:
            return False

        notification_str = "Please respond with 'y' or 'n'"
        print(notification_str)


def parse_args(args):
    help_d = {
            'desc': 'Automatically crops faces from batches of pictures',
            'input': 'Folder with images to crop are located. Default: cwd',
            'output': 'Folder where images to crop are located. Default: cwd',
            'width': 'Width of cropped files in px. Default=500',
            'height': 'Height of cropped files in px. Default=500',
            }

    parser = argparse.ArgumentParser(description=help_d['desc'])
    parser.add_argument('-o', '--output', '-p', '--path', type=output_path,
                        default=None, help=help_d['output'])
    parser.add_argument('-i', '--input', default='.', type=input_path,
                        help=help_d['input'])
    parser.add_argument('-w', '--width', type=size,
                        default=500, help=help_d['width'])
    parser.add_argument('-H', '--height',
                        type=size, default=500, help=help_d['height'])
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s version {}'.format(__version__))
    return parser.parse_args()


def cli():
    args = parse_args(sys.argv[1:])
    if args.output is None:
        if not confirmation(QUESTION_OVERWRITE):
            sys.exit()
    print('Processing images in folder:', args.input)
    main(args.input, args.output, args.height, args.width)
