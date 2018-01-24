# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import cv2
import numpy as np
import os
import shutil
import sys

from .__version__ import __version__

FIXEXP = True  # Flag to fix underexposition
MINFACE = 8  # Minimum face size ratio; too low and we get false positives
INCREMENT = 0.06
GAMMA_THRES = 0.001
GAMMA = 0.90
FACE_RATIO = 6  # Face / padding ratio
QUESTION_OVERWRITE = "Overwrite image files?"
FILETYPES = ['.jpg', '.jpeg', '.bmp', '.dib', '.jp2',
             '.png', '.webp', '.pbm', '.pgm', '.ppm',
             '.sr', '.ras', '.tiff', '.tif']
INPUT_FILETYPES = FILETYPES + [s.upper() for s in FILETYPES]

# Load XML Resource
cascFile = 'haarcascade_frontalface_default.xml'
d = os.path.dirname(sys.modules['autocrop'].__file__)
cascPath = os.path.join(d, cascFile)


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
    # Some grayscale color profiles can throw errors, catch them
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    except cv2.error:
        gray = image

    # Scale the image
    height, width = (image.shape[:2])
    minface = int(np.sqrt(height**2 + width**2) / MINFACE)

    # Create the haar cascade
    faceCascade = cv2.CascadeClassifier(cascPath)

    # ====== Detect faces in the image ======
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(minface, minface),
        flags=cv2.CASCADE_FIND_BIGGEST_OBJECT | cv2.CASCADE_DO_ROUGH_SEARCH,
    )

    # Handle no faces
    if len(faces) == 0:
        return None

    # Make padding from biggest face found
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


def main(input_d, output_d, fheight=500, fwidth=500):
    """Crops folder of images to the desired height and width if a face is found

    If input_d == output_d or output_d is None, overwrites all files
    where the biggest face was found.

    Args:
        input_d (str): Directory to crop images from.
        output_d (str): Directory where cropped images are placed.
        fheight (int): Height (px) to which to crop the image.
                       Default: 500px
        fwidth (int): Width (px) to which to crop the image.
                       Default: 500px

    Side Effects:
        Creates image files in output directory.

    str, str, (int), (int) -> None
    """
    errors = 0
    files = [os.path.join(input_d, f) for f in os.listdir(input_d)
             if any(f.endswith(t) for t in INPUT_FILETYPES)]

    # Guard against calling the function directly
    assert len(files) > 0

    if output_d is not None:
        filenames = [os.path.basename(f) for f in files]
        target_files = [os.path.join(output_d, fn) for fn in filenames]
        for i, o in zip(files, target_files):
            shutil.copyfile(i, o)
        files = target_files
    else:
        output_d = input_d

    for f in files:
        filename = os.path.basename(f)

        # Perform the actual crop
        input_img = cv2.imread(f)
        image = crop(input_img, fwidth, fheight)

        # Make sure there actually was a face in there
        if isinstance(image, type(None)):
            print('No faces can be detected in {}.'.format(filename))
            errors += 1
            continue

        # Write cropfile
        output_filename = os.path.join(output_d, filename)
        cv2.imwrite(output_filename, image)

    # Stop and print status
    print(' {} files have been cropped'.format(len(files) - errors))


def input_path(p):
    """Returns absolute path, only if input is a valid directory"""
    no_folder = 'Input folder does not exist'
    no_images = 'Input folder does not contain any image files'
    p = os.path.abspath(p)
    if not os.path.isdir(p):
        raise argparse.ArgumentTypeError(no_folder)
    filetypes = set(os.path.splitext(f)[-1] for f in os.listdir(p))
    if not any(t in INPUT_FILETYPES for t in filetypes):
        raise argparse.ArgumentTypeError(no_images)
    else:
        return p


def output_path(p):
    """Returns absolute path, if input is a valid directory name.
    If directory doesn't exist, creates it."""
    p = os.path.abspath(p)
    if not os.path.isdir(p):
        os.makedirs(p)
    return p


def size(i):
    """Returns valid only if input is a positive integer under 1e5"""
    error = 'Invalid pixel size'
    try:
        i = int(i)
    except TypeError:
        raise argparse.ArgumentTypeError(error)
    if i > 0 and i < 1e5:
        return i
    else:
        raise argparse.ArgumentTypeError(error)


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
        True: "[Y]/n",
        False: "y/[N]",
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
            'input': '''Folder where images to crop are located.
Default: current working directory''',
            'output': '''Folder where cropped images will be placed.
Default: current working directory''',
            'width': 'Width of cropped files in px. Default=500',
            'height': 'Height of cropped files in px. Default=500',
            'y': 'Bypass any confirmation prompts',
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
    parser.add_argument('--no-confirm', action='store_true', help=help_d['y'])
    return parser.parse_args()


def cli():
    args = parse_args(sys.argv[1:])
    if not args.no_confirm:
        if args.output is None or args.input == args.output:
            if not confirmation(QUESTION_OVERWRITE):
                sys.exit()
    if args.input == args.output:
        args.output = None
    print('Processing images in folder:', args.input)
    main(args.input, args.output, args.height, args.width)
