# -*- coding: utf-8 -*-

"""Tests for autocrop"""

import sys
import shutil
from glob import glob

import cv2
import numpy as np

from autocrop.autocrop import gamma, crop, main, cli


def test_gamma_brightens_image():
    """This function is so tightly coupled to cv2 it's probably useless.
    Still might flag cv2 or numpy boo-boos."""
    matrix = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    expected = np.uint8([[15, 22, 27], [31, 35, 39], [42, 45, 47]])
    np.testing.assert_array_equal(gamma(img=matrix, correction=0.5), expected)


def test_crop_noise_returns_none():
    loc = 'tests/data/noise.png'
    noise = cv2.imread(loc)
    assert crop(noise) is None


def test_obama_has_a_face():
    loc = 'tests/data/obama.jpg'
    obama = cv2.imread(loc)
    assert len(crop(obama, 500, 500)) == 500


def test_cli_default_args():
    # TODO: Copy images to data/copy
    input_loc = 'tests/data/copy'
    output_loc = 'tests/data/crop'
    sys.argv = ['autocrop', '-i', input_loc, '-p', output_loc]
    cli()
    assert len(glob(output_loc)) == 7


def test_uppercase_filetypes():
    assert main() == main()
