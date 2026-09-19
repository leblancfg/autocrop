"""Per-crop values shared by the Python API and CLI serialization."""

from dataclasses import dataclass, field

from .types import ImageArray as ImageArray


@dataclass(frozen=True)
class ImageSize:
    width: int
    height: int


@dataclass(frozen=True)
class Rectangle:
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class DetectedFace:
    box: Rectangle
    score: float | None = None
    landmarks: tuple[Point, ...] = ()


@dataclass
class DetectorDiagnostics:
    name: str
    settings: dict[str, str | int | float | None] = field(default_factory=dict)


@dataclass
class CropDiagnostics:
    detector: DetectorDiagnostics
    requested_output_dimensions: ImageSize
    resize: bool
    face_percent: int
    input_dimensions: ImageSize | None = None
    faces: tuple[DetectedFace, ...] = ()
    selected_face_index: int | None = None
    crop_rectangle: Rectangle | None = None
    actual_output_dimensions: ImageSize | None = None
    error: str | None = None


@dataclass(eq=False)
class CropResult:
    """A crop attempt. Check image, not the truthiness of this record, for success."""

    image: ImageArray | None
    diagnostics: CropDiagnostics
