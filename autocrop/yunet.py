import os
from importlib.resources import files

import cv2
import numpy as np

from .constants import YUNET_MODEL
from .diagnostics import DetectedFace, ImageArray, Point, Rectangle
from .migration import migration_message


def decode_detections(rows: ImageArray) -> tuple[DetectedFace, ...]:
    """Interpret detector rows once, before crop geometry or diagnostics use them."""
    faces = []
    for row in rows:
        landmarks: tuple[Point, ...] = ()
        if len(row) == 15 and np.isfinite(row[4:14]).all():
            landmarks = tuple(Point(float(row[i]), float(row[i + 1])) for i in range(4, 14, 2))
        faces.append(
            DetectedFace(
                box=Rectangle(*(float(value) for value in row[:4])),
                score=float(row[-1]) if len(row) in (5, 15) else None,
                landmarks=landmarks,
            )
        )
    return tuple(faces)


class YuNetDetector:
    """OpenCV YuNet face detector using FaceDetectorYN."""

    def __init__(
        self,
        model_path: str | os.PathLike[str] | None = None,
        score_threshold: float = 0.6,
        nms_threshold: float = 0.3,
        top_k: int = 5000,
    ) -> None:
        if model_path is None:
            model_path = str(files("autocrop").joinpath(YUNET_MODEL))
        self.model_path = model_path
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.top_k = top_k
        self._detector: cv2.FaceDetectorYN | None = None
        self._input_size: tuple[int, int] | None = None

    def detect(self, image: ImageArray, *, details: bool = False) -> ImageArray:
        """Return boxes, or full detection rows (box, landmarks, score)."""
        if not hasattr(cv2, "FaceDetectorYN_create"):
            raise RuntimeError(
                migration_message(
                    "Face detection requires opencv-python-headless>=4.8,<5. "
                    "Check for old or conflicting OpenCV packages in this environment.",
                    "dependencies",
                )
            )
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                migration_message(
                    f"Face detector model not found: {self.model_path}. "
                    "Check your custom model path, or reinstall autocrop to restore the bundled model.",
                    "dependencies",
                )
            )

        img_height, img_width = image.shape[:2]
        input_size = (img_width, img_height)
        if self._detector is None:
            self._detector = cv2.FaceDetectorYN_create(
                os.fspath(self.model_path),
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
            return np.empty((0, 15 if details else 4), dtype=np.float32 if details else np.int32)
        if details:
            return faces.astype(np.float32)
        return faces[:, :4].astype(np.int32)
