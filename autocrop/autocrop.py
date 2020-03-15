# -*- coding: utf-8 -*-

from __future__ import print_function, division

import cv2
import numpy as np
import os
import sys
from PIL import Image

from .constants import (
    MINFACE,
    GAMMA_THRES,
    GAMMA,
    CV2_FILETYPES,
    PILLOW_FILETYPES,
    CASCFILE,
)

COMBINED_FILETYPES = CV2_FILETYPES + PILLOW_FILETYPES
INPUT_FILETYPES = COMBINED_FILETYPES + [s.upper() for s in COMBINED_FILETYPES]


class ImageReadError(BaseException):
    """Custom exception to catch an OpenCV failure type"""

    pass


def gamma(img, correction):
    """Simple gamma correction to brighten faces"""
    img = cv2.pow(img / 255.0, correction)
    return np.uint8(img * 255)


def check_underexposed(image, gray):
    """Returns the (cropped) image with GAMMA applied if underexposition
    is detected."""
    uexp = cv2.calcHist([gray], [0], None, [256], [0, 256])
    if sum(uexp[-26:]) < GAMMA_THRES * sum(uexp):
        image = gamma(image, GAMMA)
    return image


def check_positive_scalar(num):
    """Returns True if value if a positive scalar"""
    if num > 0 and not isinstance(num, str) and np.isscalar(num):
        return int(num)
    raise ValueError("A positive scalar is required")


def check_valid_pad_dict(dic):
    """Returns dic if valid, else raises ValueError"""
    valid_keys = {
        "pad_top",
        "pad_right",
        "pad_bottom",
        "pad_left",
    }
    error = "Padding arguments must use keys {} and be positive scalars".format(valid_keys)
    conditions = []
    conditions.append(isinstance(dic, dict))
    conditions.append(len(dic) == 4)
    conditions.append(set(dic.keys()) == valid_keys)
    conditions.append(all(check_positive_scalar(n) for n in dic.values()))
    if not all(conditions):
        raise ValueError(error)
    return dic


def open_file(input_filename):
    """Given a filename, returns a numpy array"""
    extension = os.path.splitext(input_filename)[1].lower()

    if extension in CV2_FILETYPES:
        # Try with cv2
        return cv2.imread(input_filename)
    if extension in PILLOW_FILETYPES:
        # Try with PIL
        with Image.open(input_filename) as img_orig:
            return np.asarray(img_orig)
    return None


class Cropper(object):
    """
    Crops the largest detected face from images.

    This class uses the CascadeClassifier from OpenCV to
    perform the `crop` by taking in either a filepath or
    Numpy array, and returning a Numpy array. By default,
    also provides a slight gamma fix to lighten the face
    in its new context.

    Parameters:
    -----------

    width : int, default=500
        The width of the resulting array.
    height : int, default=500
        The height of the resulting array.
    padding: int or dict, default=50
        Number of pixels to pad around the largest detected
        face. Expected padding dict: {
            "pad_top": int,
            "pad_right": int,
            "pad_bottom": int,
            "pad_left": int
            }
    face_percent: int, default=50
        Aka zoom factor. Percent of the overall size of
        the cropped image containing the detected coordinates.
    fix_gamma: bool, default=True
        Cropped faces are often underexposed when taken
        out of their context. If under a threshold, sets the
        gamma to 0.9.
    """

    def __init__(
        self, width=500, height=500, padding=50, face_percent=50, fix_gamma=True
    ):
        # Size
        self.height = check_positive_scalar(height)
        self.width = check_positive_scalar(width)

        # Padding
        if isinstance(padding, int):
            pad = check_positive_scalar(padding)
            self.pad_top = pad
            self.pad_right = pad
            self.pad_bottom = pad
            self.pad_left = pad
        else:
            pad = check_valid_pad_dict(padding)
            self.pad_top = pad["pad_top"]
            self.pad_right = pad["pad_right"]
            self.pad_bottom = pad["pad_bottom"]
            self.pad_left = pad["pad_left"]

        # Gamma
        self.gamma = fix_gamma

        # Face Percent
        if face_percent > 100:
            fp_error = "The face_percent argument must be between 0 and 100"
            raise ValueError(fp_error)
        self.face_percent = check_positive_scalar(face_percent)

        # XML Resource
        directory = os.path.dirname(sys.modules["autocrop"].__file__)
        self.casc_path = os.path.join(directory, CASCFILE)

    def crop(self, path_or_array):
        """Given a file path or np.ndarray image with a face,
        returns cropped np.ndarray around the largest detected
        face.

        Parameters
        ----------
        path_or_array : {str, np.ndarray}
            The filepath or numpy array of the image.

        Returns
        -------
        image : {np.ndarray, None}
            A cropped numpy array if face detected, else None.
        """
        if isinstance(path_or_array, str):
            image = open_file(path_or_array)
        else:
            image = path_or_array

        # Some grayscale color profiles can throw errors, catch them
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        except cv2.error:
            gray = image

        # Scale the image
        try:
            img_height, img_width = image.shape[:2]
        except AttributeError:
            raise ImageReadError
        minface = int(np.sqrt(img_height ** 2 + img_width ** 2) / MINFACE)

        # Create the haar cascade
        face_cascade = cv2.CascadeClassifier(self.casc_path)

        # ====== Detect faces in the image ======
        faces = face_cascade.detectMultiScale(
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
        pos = self._crop_positions(img_height, img_width, x, y, w, h,)
        # ====== Actual cropping ======
        image = image[pos[0] : pos[1], pos[2] : pos[3]]

        # Resize
        image = cv2.resize(
            image, (self.width, self.height), interpolation=cv2.INTER_AREA
        )

        # Underexposition
        if self.gamma:
            image = check_underexposed(image, gray)
        return image

    def _crop_positions(
        self, img_height, img_width, x, y, w, h,
    ):
        """Given face coordinates, returns coordinates for which
        to crop on given padding and face_percent parameters."""
        # Adjust output height based on percent
        aspect_ratio = float(self.width) / float(self.height)
        height_crop = h * 100.0 / self.face_percent
        width_crop = aspect_ratio * float(height_crop)

        # Calculate padding by centering face
        xpad = (width_crop - w) / 2
        ypad = (height_crop - h) / 2

        # Calc. positions of crop
        h1 = float(x - (xpad * self.pad_left / (self.pad_left + self.pad_right)))
        h2 = float(x + w + (xpad * self.pad_right / (self.pad_left + self.pad_right)))
        v1 = float(y - (ypad * self.pad_top / (self.pad_top + self.pad_bottom)))
        v2 = float(y + h + (ypad * self.pad_bottom / (self.pad_top + self.pad_bottom)))

        # Determine padding ratios
        left_pad_ratio = self.pad_left / (self.pad_left + self.pad_right)
        right_pad_ratio = self.pad_left / (self.pad_left + self.pad_right)
        top_pad_ratio = self.pad_top / (self.pad_top + self.pad_bottom)
        bottom_pad_ratio = self.pad_bottom / (self.pad_top + self.pad_bottom)

        # Calculate largest bounds with padding ratios
        delta_h = 0.0
        if h1 < 0:
            delta_h = abs(h1) / left_pad_ratio

        if h2 > img_width:
            delta_h = max(delta_h, (h2 - img_width) / right_pad_ratio)

        delta_v = 0.0 if delta_h <= 0.0 else delta_h / aspect_ratio

        if v1 < 0:
            delta_v = max(delta_v, abs(v1) / top_pad_ratio)

        if v2 > img_height:
            delta_v = max(delta_v, (v2 - img_height) / bottom_pad_ratio)

        delta_h = max(delta_h, delta_v * aspect_ratio)

        # Adjust crop values accordingly
        h1 += delta_h * left_pad_ratio
        h2 -= delta_h * right_pad_ratio
        v1 += delta_v * top_pad_ratio
        v2 -= delta_v * bottom_pad_ratio

        return [int(v1), int(v2), int(h1), int(h2)]
