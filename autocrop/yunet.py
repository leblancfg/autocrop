import os
from importlib.resources import files

import cv2
import numpy as np

from .constants import YUNET_MODEL


class YuNetDetector:
    """OpenCV YuNet face detector using FaceDetectorYN."""

    def __init__(
        self,
        model_path=None,
        score_threshold=0.6,
        nms_threshold=0.3,
        top_k=5000,
    ):
        if model_path is None:
            model_path = str(files("autocrop").joinpath(YUNET_MODEL))
        self.model_path = model_path
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.top_k = top_k
        self._detector = None
        self._input_size = None

    def detect(self, image):
        if not hasattr(cv2, "FaceDetectorYN_create"):
            raise RuntimeError("OpenCV FaceDetectorYN is not available")
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(self.model_path)

        img_height, img_width = image.shape[:2]
        input_size = (img_width, img_height)
        if self._detector is None:
            self._detector = cv2.FaceDetectorYN_create(
                self.model_path,
                "",
                input_size,
                self.score_threshold,
                self.nms_threshold,
                self.top_k,
            )
            self._input_size = input_size
        elif input_size != self._input_size:
            self._detector.setInputSize(input_size)
            self._input_size = input_size

        _, faces = self._detector.detect(image)
        if faces is None:
            return np.empty((0, 4), dtype=np.int32)
        return faces[:, :4].astype(np.int32)
