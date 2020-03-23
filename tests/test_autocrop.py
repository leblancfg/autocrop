"""Tests for autocrop"""

import pytest  # noqa: F401
import cv2
import numpy as np

from autocrop.autocrop import gamma, Cropper, ImageReadError


def test_gamma_brightens_image():
    """This function is so tightly coupled to cv2 it's probably useless.
    Still might flag cv2 or numpy boo-boos."""
    matrix = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    expected = np.uint8([[15, 22, 27], [31, 35, 39], [42, 45, 47]])
    np.testing.assert_array_equal(gamma(img=matrix, correction=0.5), expected)


def test_crop_noise_returns_none():
    loc = "tests/data/noise.png"
    noise = cv2.imread(loc)
    c = Cropper()
    assert c.crop(noise) is None


def test_obama_has_a_face():
    loc = "tests/data/obama.jpg"
    obama = cv2.imread(loc)
    c = Cropper()
    assert len(c.crop(obama)) == 500


def test_open_file_invalid_filetype_returns_None():
    c = Cropper()
    with pytest.raises(ImageReadError) as e:
        c.crop("asdf")
    assert e.type == ImageReadError
    assert "ImageReadError" in str(e)


@pytest.mark.parametrize(
    "values, expected_result",
    [
        ([500, 500, 50, 50, 50, 50], [37, 112, 37, 112]),
        ([500, 500, 50, 0, 0, 0], [0, 0, 50, 50]),
    ],
)
def test_adjust_boundaries(values, expected_result):
    """Trigger the following: [h1 < 0, h2 > imgw, v1 < 0, v2 > imgh]"""
    # TODO: the padding code section is critically broken and
    # needs to be rewritten anyways. This section is more of
    # the draft of the proper testing section once the code is
    # fixed.
    imgh, imgw, h1, h2, v1, v2 = values
    c = Cropper()
    result = c._crop_positions(imgh, imgw, h1, h2, v1, v2)
    assert result == expected_result
