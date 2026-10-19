"""Serialize CLI reports and write them without damaging image files."""

import json
import os
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import BinaryIO, Iterable

from .diagnostics import CropDiagnostics


@dataclass
class CliReport:
    input: str
    output: str
    output_path: str | None = None
    image_format: str | None = None
    crop: CropDiagnostics | None = None
    error: str | None = None
    message: str | None = None
    timings: dict[str, float] = field(default_factory=dict)

    @property
    def failure(self) -> str | None:
        return self.error or (self.crop.error if self.crop is not None else None)

    def to_dict(self) -> dict[str, object]:
        """Keep the CLI's flat JSON schema; conversion happens only at this boundary."""
        return {
            **(asdict(self.crop) if self.crop is not None else {}),
            "input": self.input,
            "output": self.output,
            "output_path": self.output_path,
            "image_format": self.image_format,
            "exif_orientation_handling": "applied_to_input_and_removed_from_output",
            "error": self.failure,
            "message": self.message,
            "timings": self.timings,
        }


def same_file(left: str | os.PathLike[str], right: str | os.PathLike[str]) -> bool:
    if Path(left).resolve() == Path(right).resolve():
        return True
    try:
        return os.path.samefile(left, right)
    except OSError:
        return False


def _same_stream(destination: str | os.PathLike[str], stream: BinaryIO) -> bool:
    try:
        return os.path.samestat(os.stat(destination), os.fstat(stream.fileno()))
    except (OSError, AttributeError, ValueError):
        return False


def validate_destination(
    destination: str | os.PathLike[str] | None,
    *image_paths: str | os.PathLike[str] | None,
    image_streams: Iterable[BinaryIO] = (),
) -> None:
    if not destination or destination == "-":
        return
    for path in image_paths:
        if path and path != "-" and same_file(destination, path):
            raise ValueError("JSON diagnostics must not overwrite the input or output image; choose a different path")
    if any(_same_stream(destination, stream) for stream in image_streams):
        raise ValueError("JSON diagnostics must not overwrite a redirected image stream; choose a different path")


def write(diagnostics: dict[str, object], destination: str | os.PathLike[str] | None) -> None:
    if not destination:
        return
    payload = json.dumps(diagnostics, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if destination == "-":
        print(payload, end="", file=sys.stderr)
        return
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temporary = handle.name
            handle.write(payload)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def report_error(message: object, destination: str | os.PathLike[str] | None) -> None:
    """Report pre-processing errors without mixing prose into JSON stderr."""
    if destination == "-":
        write({"error": "cli_error", "message": str(message)}, "-")
    else:
        print(message, file=sys.stderr)
