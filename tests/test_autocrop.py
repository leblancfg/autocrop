"""Tests for autocrop"""

from glob import glob
import shutil
import pytest  # noqa: F401
import cv2
import numpy as np

from autocrop.autocrop import gamma, Cropper


@pytest.fixture()
def integration():
    # Setup
    path_i = "tests/test"
    path_o = "tests/crop"
    path_r = "tests/reject"
    shutil.copytree("tests/data", path_i)
    yield

    # Teardown
    shutil.rmtree(path_i)
    for path in [path_o, path_r]:
        try:
            shutil.rmtree(path)
        except OSError:
            pass


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


def test_open_file_invalid_filetype_returns_error():
    c = Cropper()
    with pytest.raises(FileNotFoundError) as e:
        c.crop("asdf")
    assert "No such file" in str(e)


@pytest.mark.parametrize(
    "values, expected_result",
    [
        ([500, 500, 50, 50, 100, 100], [0, 200, 0, 200]),
        ([500, 500, 50, 0, 100, 100], [0, 100, 50, 150]),
        ([500, 500, 100, 100, 300, 300], [0, 500, 0, 500]),
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


@pytest.mark.slow
@pytest.mark.parametrize(
    "height, width",
    [(500, 500), (900, 500), (500, 900), (1000, 1200)],
)
def test_detect_face_in_cropped_image(height, width, integration):
    """An image cropped by Cropper should have a face detectable.
    This defends us against image warping or crops outside the region
    of interest.
    """
    c = Cropper(height=height, width=width)
    faces = [f for f in glob("tests/test/*") if not f.endswith("md")]
    print(faces)
    for face in faces:
        try:
            img_array = c.crop(face)
        except (AttributeError, TypeError):
            pass
        if img_array is not None:
            assert c.crop(img_array) is not None


@pytest.mark.parametrize("resize", [True, False])
def test_resize(resize, integration):
    c = Cropper(resize=resize)
    face = "tests/test/obama.jpg"
    img_array = c.crop(face)
    if resize:
        assert img_array.shape == (500, 500, 3)
    else:
        assert img_array.shape == (430, 430, 3)


@pytest.mark.parametrize("face_percent", [0, 101, "asdf"])
def test_face_percent(face_percent):
    if isinstance(face_percent, str):
        with pytest.raises(TypeError) as e:
            Cropper(face_percent=face_percent)
            assert "TypeError" in str(e)
    else:
        with pytest.raises(ValueError) as e:
            Cropper(face_percent=face_percent)
            assert "argument must be between 0 and 1" in str(e)


def test_transparent_png(integration):
    c = Cropper()
    img = c.crop("tests/test/expo_67.png")

    # Make sure the first pixel is transparent
    assert img[0, 0, 3] == 0
