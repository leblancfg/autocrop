"""Face roll correction on detector-independent geometry."""

import math

import cv2
import numpy as np

from .diagnostics import AlignmentDiagnostics, DetectedFace, ImageArray, Rectangle


def eye_angle(face: DetectedFace) -> float | None:
    if len(face.landmarks) < 2:
        return None
    eye_a, eye_b = face.landmarks[:2]
    if not all(math.isfinite(value) for value in (eye_a.x, eye_a.y, eye_b.x, eye_b.y)):
        return None
    dx, dy = eye_b.x - eye_a.x, eye_b.y - eye_a.y
    if dx == 0 and dy == 0:
        return None
    # An eye line is undirected: reversing landmark order must not add 180°.
    return (math.degrees(math.atan2(dy, dx)) + 90) % 180 - 90


def transform_box(box: Rectangle, matrix: ImageArray, image_width: int, image_height: int) -> Rectangle:
    x, y, w, h = box.x, box.y, box.width, box.height
    corners = np.array([[x, y, 1], [x + w, y, 1], [x, y + h, 1], [x + w, y + h, 1]])
    transformed = corners @ matrix.T
    left, top = transformed.min(axis=0)
    right, bottom = transformed.max(axis=0)
    left, right = np.clip([left, right], 0, image_width)
    top, bottom = np.clip([top, bottom], 0, image_height)
    return Rectangle(float(left), float(top), float(right - left), float(bottom - top))


def align_face(
    image: ImageArray,
    face: DetectedFace,
    max_rotation: float,
) -> tuple[ImageArray, Rectangle, AlignmentDiagnostics]:
    angle = eye_angle(face)
    metadata = AlignmentDiagnostics(enabled=True, angle_degrees=angle, reason="missing_landmarks")
    if angle is None:
        return image, face.box, metadata
    if abs(angle) > max_rotation:
        metadata.reason = "rotation_limit"
        return image, face.box, metadata
    if abs(angle) < 0.1:
        metadata.reason = "already_level"
        return image, face.box, metadata

    height, width = image.shape[:2]
    box = face.box
    center = (box.x + box.width / 2, box.y + box.height / 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    aligned = cv2.warpAffine(
        image,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )
    metadata.applied = True
    metadata.rotation_degrees = angle
    metadata.affine_matrix = tuple(tuple(float(matrix[i, j]) for j in range(3)) for i in range(2))
    metadata.reason = None
    return aligned, transform_box(face.box, matrix, width, height), metadata
