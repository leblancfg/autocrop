"""Alignment geometry and per-call result records."""

import io
import json
import sys
from dataclasses import asdict

import cv2
import numpy as np
import pytest
from PIL import Image

from autocrop import Cropper
from autocrop.alignment import align_face, eye_angle
from autocrop.cli import command_line_interface
from autocrop.yunet import YuNetDetector, decode_detections


def tilted_face():
    return np.array([20, 20, 40, 40, 30, 35, 50, 45, 40, 45, 32, 55, 48, 55, 0.9], dtype=np.float32)


class Detector:
    def detect(self, image):
        return np.array([tilted_face()])


def test_eye_line_is_independent_of_landmark_order():
    face = tilted_face()
    assert eye_angle(decode_detections([face])[0]) == pytest.approx(26.565, abs=0.001)
    face[4:8] = face[[6, 7, 4, 5]]
    assert eye_angle(decode_detections([face])[0]) == pytest.approx(26.565, abs=0.001)


def test_rotation_levels_eyes_and_maps_crop_coordinates():
    source = np.zeros((100, 100, 3), dtype=np.uint8)
    cropper = Cropper(align=True, face_detector=Detector(), resize=False)
    result = cropper.crop(source)
    metadata = result.diagnostics
    alignment = metadata.alignment
    assert alignment.applied is True
    assert metadata.crop_coordinate_space == "aligned_input"
    assert metadata.faces[0].score == pytest.approx(0.9)
    matrix = np.array(alignment.affine_matrix)
    eyes = tilted_face()[4:8].reshape(2, 2)
    transformed = np.column_stack([eyes, np.ones(2)]) @ matrix.T
    assert transformed[0, 1] == pytest.approx(transformed[1, 1])
    rectangle = metadata.crop_rectangle
    assert result.image.shape[:2] == (rectangle.height, rectangle.width)
    json.dumps(asdict(metadata), allow_nan=False)


def test_alignment_default_does_not_rotate(monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail("alignment was requested when disabled")

    monkeypatch.setattr(cv2, "warpAffine", fail)
    result = Cropper(face_detector=Detector()).crop(np.zeros((100, 100, 3), dtype=np.uint8))
    assert result.diagnostics.alignment.reason == "disabled"
    assert result.diagnostics.crop_coordinate_space == "oriented_input"


@pytest.mark.parametrize(
    "eyes, reason",
    [
        ([40, 20, 40, 70], "rotation_limit"),
        ([30, 35, 50, 35], "already_level"),
        ([30, 35, 30, 35], "missing_landmarks"),
        ([float("nan"), 35, 50, 45], "missing_landmarks"),
    ],
)
def test_skipped_alignment(eyes, reason):
    face = tilted_face()
    face[4:8] = eyes
    source = np.zeros((100, 100, 3), dtype=np.uint8)
    image, box, metadata = align_face(source, decode_detections([face])[0], 30)
    assert image is source
    assert metadata.reason == reason
    assert metadata.applied is False


def test_box_only_detector_skips_alignment():
    class BoxDetector:
        def detect(self, image):
            return np.array([[20, 20, 40, 40]])

    result = Cropper(align=True, face_detector=BoxDetector()).crop(
        np.zeros((100, 100, 3), dtype=np.uint8),
    )
    assert result.image is not None
    assert result.diagnostics.alignment.reason == "missing_landmarks"
    assert result.diagnostics.faces[0].score is None


@pytest.mark.parametrize("resize", [False, True])
def test_alignment_preserves_alpha_and_return_contract(resize):
    source = np.zeros((100, 100, 4), dtype=np.uint8)
    source[:, :, 3] = 127
    cropper = Cropper(width=40, height=40, align=True, resize=resize, face_detector=Detector())
    first = cropper.crop(source.copy())
    result = cropper.crop(source.copy())
    np.testing.assert_array_equal(first.image, result.image)
    assert result.image.shape[-1] == 4
    assert np.all(result.image[:, :, 3] == 127)
    if resize:
        assert result.image.shape[:2] == (40, 40)


@pytest.mark.parametrize("value", [0, -1, 91, float("nan"), float("inf")])
def test_rotation_limit_is_validated(value):
    with pytest.raises(ValueError, match="max_rotation"):
        Cropper(max_rotation=value)


def test_fractional_rotation_limit():
    assert Cropper(max_rotation=0.5).max_rotation == 0.5


def test_real_detector_details_include_landmarks_and_score():
    image = cv2.imread("tests/data/obama.jpg")
    detector = YuNetDetector()
    faces = detector.detect(image, details=True)
    assert faces.shape[1] == 15
    assert 0 <= faces[0, -1] <= 1
    np.testing.assert_array_equal(detector.detect(image), faces[:, :4].astype(np.int32))
    result = Cropper(align=True).crop(image)
    assert result.image.shape == (500, 500, 3)
    assert result.diagnostics.faces[0].score == pytest.approx(float(faces[0, -1]))
    assert result.diagnostics.alignment.applied is True


@pytest.mark.parametrize("stdin_mode", [False, True])
def test_cli_alignment_and_json_together(stdin_mode, monkeypatch, capsys):
    from autocrop import cli

    output = io.BytesIO()
    monkeypatch.setattr(cli, "output_bytes", lambda image, stream, fmt: Image.fromarray(image).save(output, format=fmt))
    if stdin_mode:
        monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(open("tests/data/obama.jpg", "rb").read())))
    monkeypatch.setattr(
        sys,
        "argv",
        ["autocrop", "-" if stdin_mode else "tests/data/obama.jpg", "--align", "--json", "-"],
    )
    with pytest.raises(SystemExit) as exc:
        command_line_interface()
    assert exc.value.code == 0
    metadata = json.loads(capsys.readouterr().err)
    assert metadata["alignment"]["applied"] is True
    with Image.open(io.BytesIO(output.getvalue())) as image:
        assert image.size == (500, 500)


def test_help_uses_user_facing_alignment_description(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["autocrop", "--help"])
    with pytest.raises(SystemExit) as exc:
        command_line_interface()
    assert exc.value.code == 0
    help_text = " ".join(capsys.readouterr().out.split())
    assert "Rotate faces so they're level using eye landmarks before cropping" in help_text
    assert "YuNet" not in help_text
