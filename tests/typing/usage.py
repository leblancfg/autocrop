"""Checked by ty, not executed: examples of the supported downstream API."""

from dataclasses import asdict

import numpy as np
from typing_extensions import assert_type

from autocrop import CropDiagnostics, Cropper, CropResult
from autocrop.autocrop import FaceDetector
from autocrop.diagnostics import Rectangle
from autocrop.types import ImageArray


class BoxesOnlyDetector:
    def detect(self, image: ImageArray) -> ImageArray:
        return np.array([[0, 0, 10, 10]], dtype=np.int32)


def use_cropper(source: str | ImageArray) -> CropResult:
    detector: FaceDetector = BoxesOnlyDetector()
    cropper = Cropper(face_detector=detector)
    result = cropper.crop(source)
    assert_type(result, CropResult)
    assert_type(result.image, ImageArray | None)
    assert_type(result.diagnostics, CropDiagnostics)
    assert_type(result.diagnostics.crop_rectangle, Rectangle | None)
    if result.image is not None:
        print(result.image.shape)
    if result.diagnostics.crop_rectangle is not None:
        print(result.diagnostics.crop_rectangle.width)
    print(asdict(result.diagnostics))
    return result


def reject_old_api() -> None:
    cropper = Cropper()
    cropper.crop("portrait.jpg", diagnostics=True)  # ty: ignore[unknown-argument]
    old_array: ImageArray = cropper.crop("portrait.jpg")  # ty: ignore[invalid-assignment]
    print(old_array)
