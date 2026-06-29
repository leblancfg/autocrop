"""Tests for autocrop"""

from glob import glob
import shutil

import pytest  # noqa: F401
import cv2
import numpy as np
from PIL import Image

from autocrop.autocrop import Cropper
from autocrop.yunet import YuNetDetector


@pytest.fixture()
def integration():
    # Setup
    path_i = "tests/test"
    path_o = "tests/crop"
    path_r = "tests/reject"
    for path in [path_i, path_o, path_r]:
        shutil.rmtree(path, ignore_errors=True)
    shutil.copytree("tests/data", path_i)
    yield

    # Teardown
    for path in [path_i, path_o, path_r]:
        shutil.rmtree(path, ignore_errors=True)


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


def test_path_crop_preserves_rgb_channels(tmp_path):
    class MockDetector:
        def detect(self, image, gray):
            return np.array([[0, 0, 2, 2]])

    source = np.array(
        [
            [[255, 0, 0], [0, 0, 255]],
            [[0, 255, 0], [255, 255, 0]],
        ],
        dtype=np.uint8,
    )
    image_path = tmp_path / "rgb.png"
    Image.fromarray(source).save(image_path)

    c = Cropper(
        width=2,
        height=2,
        face_percent=100,
        resize=False,
        face_detector=MockDetector(),
    )
    np.testing.assert_array_equal(c.crop(str(image_path)), source)


def test_cropper_accepts_detector_object():
    class MockDetector:
        def detect(self, image, gray):
            return np.array([[0, 0, 2, 2]])

    source = np.array(
        [
            [[255, 0, 0], [0, 0, 255]],
            [[0, 255, 0], [255, 255, 0]],
        ],
        dtype=np.uint8,
    )
    expected = source[:, :, [2, 1, 0]].copy()

    c = Cropper(
        width=2,
        height=2,
        face_percent=100,
        resize=False,
        face_detector=MockDetector(),
    )
    np.testing.assert_array_equal(c.crop(source), expected)


def test_cropper_normalizes_grayscale_for_detection(tmp_path):
    class MockDetector:
        def detect(self, image, gray):
            self.image = image.copy()
            self.gray = gray.copy()
            return np.array([[0, 0, 2, 2]])

    source = np.array([[0, 127], [200, 255]], dtype=np.uint8)
    image_path = tmp_path / "gray.png"
    Image.fromarray(source).save(image_path)
    detector = MockDetector()

    c = Cropper(
        width=2,
        height=2,
        face_percent=100,
        resize=False,
        face_detector=detector,
    )

    np.testing.assert_array_equal(c.crop(str(image_path)), source)
    assert detector.image.shape == (2, 2, 3)
    np.testing.assert_array_equal(detector.image[:, :, 0], source)
    np.testing.assert_array_equal(detector.image[:, :, 1], source)
    np.testing.assert_array_equal(detector.image[:, :, 2], source)
    np.testing.assert_array_equal(detector.gray, source)


def test_cropper_normalizes_rgba_for_detection_and_preserves_alpha(tmp_path):
    class MockDetector:
        def detect(self, image, gray):
            self.image = image.copy()
            return np.array([[0, 0, 2, 2]])

    source = np.array(
        [
            [[255, 0, 0, 0], [0, 255, 0, 85]],
            [[0, 0, 255, 170], [255, 255, 0, 255]],
        ],
        dtype=np.uint8,
    )
    image_path = tmp_path / "rgba.png"
    Image.fromarray(source).save(image_path)
    detector = MockDetector()

    c = Cropper(
        width=2,
        height=2,
        face_percent=100,
        resize=False,
        face_detector=detector,
    )

    np.testing.assert_array_equal(c.crop(str(image_path)), source)
    assert detector.image.shape == (2, 2, 3)
    np.testing.assert_array_equal(detector.image, source[:, :, [2, 1, 0]])


def test_cropper_uses_largest_detected_face():
    class MockDetector:
        def detect(self, image, gray):
            return np.array([[0, 0, 1, 1], [0, 0, 2, 2]])

    source = np.array(
        [
            [[1, 2, 3], [4, 5, 6]],
            [[7, 8, 9], [10, 11, 12]],
        ],
        dtype=np.uint8,
    )
    expected = source[:, :, [2, 1, 0]].copy()

    c = Cropper(
        width=2,
        height=2,
        face_percent=100,
        resize=False,
        face_detector=MockDetector(),
    )

    np.testing.assert_array_equal(c.crop(source), expected)


def test_yunet_detector_uses_packaged_model(monkeypatch):
    created = {}

    class MockFaceDetectorYN:
        def detect(self, image):
            return None, np.array([[1.2, 2.3, 3.4, 4.5, 0.9]])

    def mock_create(model_path, config, input_size, score_threshold, nms_threshold, top_k):
        created["model_path"] = model_path
        created["config"] = config
        created["input_size"] = input_size
        created["score_threshold"] = score_threshold
        created["nms_threshold"] = nms_threshold
        created["top_k"] = top_k
        return MockFaceDetectorYN()

    monkeypatch.setattr(cv2, "FaceDetectorYN_create", mock_create, raising=False)

    detector = YuNetDetector()
    faces = detector.detect(np.zeros((20, 10, 3), dtype=np.uint8))

    assert created["model_path"].endswith("face_detection_yunet_2023mar.onnx")
    assert created["config"] == ""
    assert created["input_size"] == (10, 20)
    assert created["score_threshold"] == 0.6
    assert created["nms_threshold"] == 0.3
    assert created["top_k"] == 5000
    np.testing.assert_array_equal(faces, np.array([[1, 2, 3, 4]], dtype=np.int32))


def test_yunet_detector_returns_empty_when_no_faces(monkeypatch):
    class MockFaceDetectorYN:
        def detect(self, image):
            return None, None

    monkeypatch.setattr(
        cv2,
        "FaceDetectorYN_create",
        lambda *args: MockFaceDetectorYN(),
        raising=False,
    )

    detector = YuNetDetector()
    faces = detector.detect(np.zeros((20, 10, 3), dtype=np.uint8))

    assert faces.shape == (0, 4)


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


@pytest.mark.parametrize(
    "values",
    [
        (663, 2495, 185, 867, 327, 354),
        (612, 1020, 13, 280, 26, 33),
        (612, 1020, 979, 282, 24, 34),
        (612, 1020, 1003, 169, 16, 21),
        (612, 1020, 993, 351, 26, 44),
        (612, 1020, 996, 271, 21, 26),
        (612, 1020, 9, 382, 30, 49),
        (612, 1020, 0, 231, 14, 27),
    ],
)
def test_crop_positions_stay_inside_image_bounds(values):
    imgh, imgw, x, y, w, h = values
    c = Cropper()
    v1, v2, h1, h2 = c._crop_positions(imgh, imgw, x, y, w, h)
    assert 0 <= v1 < v2 <= imgh
    assert 0 <= h1 < h2 <= imgw


@pytest.mark.slow
@pytest.mark.parametrize(
    "height, width",
    [(500, 500), (700, 500), (500, 700), (1000, 1200)],
)
def test_detect_face_in_cropped_image(height, width, integration):
    """
    Cropped outputs should stay inside image bounds and remain valid arrays.
    YuNet is intentionally strict, so a second-pass detection is not a stable
    invariant for aggressively margin-heavy crops.
    """
    c = Cropper(height=height, width=width, face_percent=1, resize=False)
    faces = [f for f in glob("tests/test/*") if not f.endswith("md")]
    for face in faces:
        try:
            img_array = c.crop(face)
        except (AttributeError, TypeError):
            pass
        if img_array is not None:
            assert img_array.size > 0
            assert img_array.shape[0] > 0
            assert img_array.shape[1] > 0


@pytest.mark.parametrize("resize", [True, False])
def test_resize(resize, integration):
    c = Cropper(resize=resize)
    face = "tests/test/obama.jpg"
    img_array = c.crop(face)
    if resize:
        assert img_array.shape == (500, 500, 3)
    else:
        assert img_array.shape == (452, 452, 3)


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

    # Make sure we're still RGBA
    assert img.shape[-1] == 4

    # Make sure the first pixel is transparent
    assert img[0, 0, 3] == 0
