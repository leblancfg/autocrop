import os
import sys

import cv2
import numpy as np

from .constants import CASCFILE, MINFACE, YUNET_MODEL


VALID_DETECTORS = ("haar", "yunet")


class HaarDetector:
    """OpenCV Haar cascade face detector."""

    name = "haar"

    def __init__(self, cascade_path=None):
        if cascade_path is None:
            directory = os.path.dirname(sys.modules["autocrop"].__file__)
            cascade_path = os.path.join(directory, CASCFILE)
        self.cascade_path = cascade_path

    def detect(self, image, gray):
        img_height, img_width = image.shape[:2]
        minface = int(np.sqrt(img_height**2 + img_width**2) / MINFACE)
        face_cascade = cv2.CascadeClassifier(self.cascade_path)
        return face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(minface, minface),
            flags=cv2.CASCADE_FIND_BIGGEST_OBJECT | cv2.CASCADE_DO_ROUGH_SEARCH,
        )


class YuNetDetector:
    """OpenCV YuNet face detector using FaceDetectorYN."""

    name = "yunet"

    def __init__(
        self,
        model_path=None,
        score_threshold=0.6,
        nms_threshold=0.3,
        top_k=5000,
    ):
        if model_path is None:
            directory = os.path.dirname(sys.modules["autocrop"].__file__)
            model_path = os.path.join(directory, YUNET_MODEL)
        self.model_path = model_path
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.top_k = top_k

    def detect(self, image, gray=None):
        if not hasattr(cv2, "FaceDetectorYN_create"):
            raise RuntimeError("OpenCV FaceDetectorYN is not available")
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(self.model_path)

        img_height, img_width = image.shape[:2]
        detector = cv2.FaceDetectorYN_create(
            self.model_path,
            "",
            (img_width, img_height),
            self.score_threshold,
            self.nms_threshold,
            self.top_k,
        )
        _, faces = detector.detect(image)
        if faces is None:
            return np.empty((0, 4), dtype=np.int32)
        return faces[:, :4].astype(np.int32)


def build_detector(detector, **kwargs):
    """Build a face detector from a name or return a detector-like object."""
    if hasattr(detector, "detect"):
        return detector
    if detector == "haar":
        return HaarDetector()
    if detector == "yunet":
        return YuNetDetector(**kwargs)
    raise ValueError("detector must be one of: {}".format(", ".join(VALID_DETECTORS)))
