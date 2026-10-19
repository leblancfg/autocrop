"""Per-crop values shared by the Python API and CLI serialization."""

from dataclasses import dataclass, field
from typing import NoReturn

from .migration import migration_message
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
class AlignmentDiagnostics:
    enabled: bool = False
    applied: bool = False
    reason: str | None = "not_processed"
    angle_degrees: float | None = None
    rotation_degrees: float = 0.0
    affine_matrix: tuple[tuple[float, ...], ...] | None = None


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
    alignment: AlignmentDiagnostics = field(default_factory=AlignmentDiagnostics)
    crop_coordinate_space: str = "oriented_input"


@dataclass(eq=False)
class CropResult:
    """A crop attempt. Check image, not the truthiness of this record, for success."""

    image: ImageArray | None
    diagnostics: CropDiagnostics

    def __bool__(self) -> NoReturn:
        raise TypeError(
            migration_message("Check result.image is not None, not the truthiness of CropResult.", "python-results")
        )

    def __len__(self) -> NoReturn:
        raise TypeError(
            migration_message(
                "CropResult is not an array. Use len(result.image) after checking result.image is not None.",
                "python-results",
            )
        )

    def __iter__(self) -> NoReturn:
        raise TypeError(
            migration_message(
                "CropResult cannot be unpacked or iterated. Read result.image and result.diagnostics explicitly.",
                "python-results",
            )
        )

    def __getitem__(self, key: object) -> NoReturn:
        raise TypeError(
            migration_message(
                "CropResult is not an array or dictionary. Index result.image after checking it is not None; "
                "read diagnostics through result.diagnostics attributes.",
                "python-results",
            )
        )

    def __getattr__(self, name: str) -> NoReturn:
        raise AttributeError(
            migration_message(
                f"CropResult has no attribute {name!r}; it is not an image array. "
                "Use result.image after checking it is not None, or read result.diagnostics.",
                "python-results",
            )
        )
