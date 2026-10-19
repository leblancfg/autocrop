"""Checked by ty: the API on master before the feature PRs are applied."""

import numpy as np
from typing_extensions import assert_type

from autocrop import Cropper
from autocrop.autocrop import FaceDetector
from autocrop.types import ImageArray


class BoxesOnlyDetector:
    def detect(self, image: ImageArray) -> ImageArray:
        return np.array([[0, 0, 10, 10]], dtype=np.int32)


def use_cropper(source: str | ImageArray) -> ImageArray | None:
    detector: FaceDetector = BoxesOnlyDetector()
    cropper = Cropper(face_detector=detector)
    image = cropper.crop(source)
    assert_type(image, ImageArray | None)
    if image is not None:
        print(image.shape)
    return image
