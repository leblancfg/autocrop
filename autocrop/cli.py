# -*- coding: utf-8 -*-

from __future__ import print_function, division

import argparse
import cv2
import io
import os
import shutil
import sys

from PIL import Image

from .__version__ import __version__
from .autocrop import Cropper, ImageReadError
from .constants import (
    QUESTION_OVERWRITE,
    CV2_FILETYPES,
    PILLOW_FILETYPES,
)

COMBINED_FILETYPES = CV2_FILETYPES + PILLOW_FILETYPES
INPUT_FILETYPES = COMBINED_FILETYPES + [s.upper() for s in COMBINED_FILETYPES]


def check_padding_value(num):
    """Returns original value if positive scalar, else returns 50"""
    # For CLI backwards compatibility; Cropper already checks input
    if num is False or num < 0:
        return 50
    return num


def output(input_filename, output_filename, image):
    """Move the input file to the output location and write over it with the
    cropped image data."""
    if input_filename != output_filename:
        # Move the file to the output directory
        shutil.move(input_filename, output_filename)
    # Encode the image as an in-memory PNG
    img_png = cv2.imencode(".png", image)[1].tostring()
    # Read the PNG data
    img_new = Image.open(io.BytesIO(img_png))
    # Write the new image (converting the format to match the output
    # filename if necessary)
    img_new.save(output_filename)


def reject(input_filename, reject_filename):
    """Move the input file to the reject location."""
    if input_filename != reject_filename:
        # Move the file to the reject directory
        shutil.move(input_filename, reject_filename)


def main(
    input_d,
    output_d,
    reject_d,
    fheight=500,
    fwidth=500,
    facePercent=50,
    padUp=False,
    padDown=False,
    padLeft=False,
    padRight=False,
):
    """Crops folder of images to the desired height and width if a face is found

    If input_d == output_d or output_d is None, overwrites all files
    where the biggest face was found.

    Args:
        input_d (str): Directory to crop images from.
        output_d (str): Directory where cropped images are placed.
        reject_d (str): Directory where images that cannot be cropped are
                        placed.
        fheight (int): Height (px) to which to crop the image.
                       Default: 500px
        fwidth (int): Width (px) to which to crop the image.
                       Default: 500px
        facePercent (int) : Percentage of face from height,
                       Default: 50
    Side Effects:
        Creates image files in output directory.

    str, str, (int), (int) -> None
    """
    reject_count = 0
    output_count = 0
    input_files = [
        os.path.join(input_d, f)
        for f in os.listdir(input_d)
        if any(f.endswith(t) for t in INPUT_FILETYPES)
    ]
    if output_d is None:
        output_d = input_d
    if reject_d is None and output_d is None:
        reject_d = input_d
    if reject_d is None:
        reject_d = output_d

    # Guard against calling the function directly
    input_count = len(input_files)
    assert input_count > 0

    # Make padding dict
    padding = {
        "pad_top": check_padding_value(padUp),
        "pad_right": check_padding_value(padRight),
        "pad_bottom": check_padding_value(padDown),
        "pad_left": check_padding_value(padLeft),
    }

    # Main loop
    cropper = Cropper(
        width=fwidth, height=fheight, padding=padding, face_percent=facePercent
    )
    for input_filename in input_files:
        basename = os.path.basename(input_filename)
        output_filename = os.path.join(output_d, basename)
        reject_filename = os.path.join(reject_d, basename)

        image = None
        # Attempt the crop
        try:
            image = cropper.crop(input_filename)
        except ImageReadError:
            print("Read error:       {}".format(input_filename))
            continue

        # Did the crop produce an invalid image?
        if isinstance(image, type(None)):
            reject(input_filename, reject_filename)
            print("No face detected: {}".format(reject_filename))
            reject_count += 1
        else:
            output(input_filename, output_filename, image)
            print("Face detected:    {}".format(output_filename))
            output_count += 1

    # Stop and print status
    print(
        "{} input files, {} faces cropped, {} rejected".format(
            input_count, output_count, reject_count
        )
    )


def input_path(p):
    """Returns path, only if input is a valid directory"""
    no_folder = "Input folder does not exist"
    no_images = "Input folder does not contain any image files"
    p = os.path.abspath(p)
    if not os.path.isdir(p):
        raise argparse.ArgumentError(no_folder)
    filetypes = set(os.path.splitext(f)[-1] for f in os.listdir(p))
    if not any(t in INPUT_FILETYPES for t in filetypes):
        raise argparse.ArgumentError(no_images)
    else:
        return p


def output_path(p):
    """Returns path, if input is a valid directory name.
    If directory doesn't exist, creates it."""
    p = os.path.abspath(p)
    if not os.path.isdir(p):
        os.makedirs(p)
    return p


def size(i):
    """Returns valid only if input is a positive integer under 1e5"""
    error = "Invalid pixel size"
    try:
        i = int(i)
    except ValueError:
        raise argparse.ArgumentTypeError(error)
    if i > 0 and i < 1e5:
        return i
    else:
        raise argparse.ArgumentTypeError(error)


def compat_input(s=""):  # pragma: no cover
    """Compatibility function to permit testing for Python 2 and 3"""
    try:
        return raw_input(s)
    except NameError:
        # Py2 raw_input() renamed to input() in Py3
        return input(s)  # lgtm[py/use-of-input]


def confirmation(question):
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
    default_str = "[Y]/n"
    prompt_str = "%s %s " % (question, default_str)

    while True:
        choice = compat_input(prompt_str).lower()

        if not choice:
            return default_str
        if choice in yes_list:
            return True
        if choice in no_list:
            return False

        notification_str = "Please respond with 'y' or 'n'"
        print(notification_str)


def parse_args(args):
    help_d = {
        "desc": "Automatically crops faces from batches of pictures",
        "input": """Folder where images to crop are located. Default:
                     current working directory""",
        "output": """Folder where cropped images will be moved to.

                      Default: current working directory, meaning images are
                      cropped in place.""",
        "reject": """Folder where images that could not be cropped will be
                       moved to.

                      Default: current working directory, meaning images that
                      are not cropped will be left in place.""",
        "width": "Width of cropped files in px. Default=500",
        "height": "Height of cropped files in px. Default=500",
        "y": "Bypass any confirmation prompts",
        "facePercent": "Percentage of face to image height",
        "padUp": "Add padding up to face cropped",
        "padDown": "Add padding down to face cropped",
        "padLeft": "Add padding left to face cropped",
        "padRight": "Add padding right to face cropped",
    }

    parser = argparse.ArgumentParser(description=help_d["desc"])
    parser.add_argument(
        "-i", "--input", default=".", type=input_path, help=help_d["input"]
    )
    parser.add_argument(
        "-o",
        "--output",
        "-p",
        "--path",
        type=output_path,
        default=None,
        help=help_d["output"],
    )
    parser.add_argument(
        "-r", "--reject", type=output_path, default=None, help=help_d["reject"]
    )
    parser.add_argument("-w", "--width", type=size, default=500, help=help_d["width"])
    parser.add_argument("-H", "--height", type=size, default=500, help=help_d["height"])
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s version {}".format(__version__),
    )
    parser.add_argument("--no-confirm", action="store_true", help=help_d["y"])
    parser.add_argument("--padUp", type=size, default=False, help=help_d["padUp"])
    parser.add_argument("--padDown", type=size, default=False, help=help_d["padDown"])
    parser.add_argument("--padLeft", type=size, default=False, help=help_d["padLeft"])
    parser.add_argument("--padRight", type=size, default=False, help=help_d["padRight"])
    parser.add_argument(
        "--facePercent", type=size, default=50, help=help_d["facePercent"]
    )

    return parser.parse_args()


def command_line_interface():
    args = parse_args(sys.argv[1:])
    if not args.no_confirm:
        if args.output is None or args.input == args.output:
            if not confirmation(QUESTION_OVERWRITE):
                sys.exit()
    if args.input == args.output:
        args.output = None
    print("Processing images in folder:", args.input)
    main(
        args.input,
        args.output,
        args.reject,
        args.height,
        args.width,
        args.facePercent,
        args.padUp,
        args.padDown,
        args.padLeft,
        args.padRight,
    )
