import argparse
import io
import os
import shutil
import stat
import sys
import time
from contextlib import contextmanager
from typing import Any, BinaryIO, Iterator, NoReturn

import numpy as np
from PIL import Image, ImageOps

from . import reporting, timing
from .__version__ import __version__
from .autocrop import Cropper
from .constants import (
    INPUT_FILETYPES,
    OUTPUT_FILETYPES,
    OUTPUT_FORMATS,
    OUTPUT_FORMATS_BY_EXTENSION,
)
from .reporting import CliReport
from .types import ImageArray

ORIENTATION_EXIF_TAG = 274


class CliError(Exception):
    """A user-facing CLI error that should not produce a traceback."""


def _preserve_metadata(
    input_filename: str | os.PathLike[str],
    output_filename: str | os.PathLike[str],
    source_stat: os.stat_result,
) -> None:
    """Preserve safe filesystem metadata from the source image."""
    if input_filename != output_filename:
        shutil.copystat(input_filename, output_filename)
    os.chmod(output_filename, stat.S_IMODE(source_stat.st_mode))
    os.utime(
        output_filename,
        ns=(source_stat.st_atime_ns, source_stat.st_mtime_ns),
    )


def _image_save_kwargs(input_filename: str | os.PathLike[str]) -> dict[str, Any]:
    """Return image metadata Pillow can preserve while writing the crop."""
    save_kwargs = {}
    with Image.open(input_filename) as img_orig:
        exif = img_orig.getexif()
        if exif:
            if ORIENTATION_EXIF_TAG in exif:
                del exif[ORIENTATION_EXIF_TAG]
            if exif:
                save_kwargs["exif"] = exif.tobytes()
        if "icc_profile" in img_orig.info:
            save_kwargs["icc_profile"] = img_orig.info["icc_profile"]
    return save_kwargs


def image_for_format(image: ImageArray, image_format: str) -> Image.Image:
    """Return a Pillow image compatible with the requested output format."""
    img_new = Image.fromarray(image)
    if image_format in {"JPEG", "EPS", "PCX"} and img_new.mode in {"LA", "P", "RGBA"}:
        return img_new.convert("RGB")
    return img_new


def output(
    input_filename: str | os.PathLike[str],
    output_filename: str | os.PathLike[str],
    image: ImageArray,
    source_stat: os.stat_result | None = None,
    image_format: str | None = None,
) -> None:
    """Write cropped image data to an output file."""
    if source_stat is None:
        source_stat = os.stat(input_filename)
    if image_format is None:
        image_format = output_format(output_filename=output_filename)
    if input_filename != output_filename:
        shutil.copy(input_filename, output_filename)
    save_kwargs = _image_save_kwargs(input_filename)
    img_new = image_for_format(image, image_format)
    img_new.save(output_filename, format=image_format, **save_kwargs)
    _preserve_metadata(input_filename, output_filename, source_stat)


def output_bytes(image: ImageArray, output_stream: BinaryIO, image_format: str) -> None:
    """Write cropped image bytes to a binary stream."""
    img_new = image_for_format(image, image_format)
    img_new.save(output_stream, format=image_format)


def input_path(p: str) -> str:
    """Return path, only if input is a valid image file or stdin."""
    no_file = "Input image does not exist"
    no_image_file = "Input file type is not supported"
    if p == "-":
        return p
    p = os.path.abspath(p)
    if not os.path.exists(p):
        raise argparse.ArgumentTypeError(no_file)
    if not os.path.isfile(p) or os.path.splitext(p)[-1].lower() not in INPUT_FILETYPES:
        raise argparse.ArgumentTypeError(no_image_file)
    return p


def size(i: str | int | float) -> int:
    """Returns valid only if input is a positive integer under 1e5"""
    error = "Invalid pixel size"
    try:
        i = int(i)
    except ValueError:
        raise argparse.ArgumentTypeError(error)
    if i > 0 and i < 1e5:
        return i
    else:
        raise argparse.ArgumentTypeError(error)


def output_format(input_format: str | None = None, output_filename: str | os.PathLike[str] | None = None) -> str:
    """Return a Pillow format name for stream or file output."""
    if output_filename:
        ext = os.path.splitext(output_filename)[1].lower()
        return OUTPUT_FORMATS_BY_EXTENSION[ext]
    if input_format is not None and input_format in OUTPUT_FORMATS:
        return input_format
    return "PNG"


def validate_output_extension(output_filename: str) -> str:
    """Return output_filename if its extension is writable by autocrop."""
    extension = os.path.splitext(output_filename)[1].lower()
    if extension in OUTPUT_FILETYPES:
        return output_filename
    raise CliError(f"Output file type is not supported: {extension or output_filename}")


def empty_timings() -> dict[str, float]:
    """Return a timing map with stable keys for verbose output."""
    return {
        "imports": timing.import_seconds(),
        "read": 0.0,
        "process": 0.0,
        "write": 0.0,
        "total": 0.0,
    }


@contextmanager
def measure(timings: dict[str, float], key: str) -> Iterator[None]:
    """Measure a stage, including time spent before an exception."""
    started = time.perf_counter()
    try:
        yield
    finally:
        timings[key] += time.perf_counter() - started


def finish_timings(timings: dict[str, float], started: float) -> None:
    """Set total time, including package imports and command runtime."""
    timings["total"] = timings["imports"] + time.perf_counter() - started


def print_verbose(
    input_label: str,
    output_label: str,
    image_format: str | None,
    timings: dict[str, float],
) -> None:
    """Write human-readable verbose diagnostics to stderr."""
    print(f"Input: {input_label}", file=sys.stderr)
    print(f"Output: {output_label}", file=sys.stderr)
    if image_format:
        print(f"Format: {image_format}", file=sys.stderr)
    print(
        "Timings: "
        f"total={timings['total']:.3f}s "
        f"imports={timings['imports']:.3f}s "
        f"read={timings['read']:.3f}s "
        f"process={timings['process']:.3f}s "
        f"write={timings['write']:.3f}s",
        file=sys.stderr,
    )


def cropper_array_from_pillow_image(img_orig: Image.Image) -> ImageArray:
    """
    Return an array in the color-channel order expected by Cropper.crop(np.ndarray).

    Cropper treats ndarray inputs as OpenCV-style BGR/BGRA and converts them back
    to RGB/RGBA before returning. Pillow decodes stream input as RGB/RGBA, so swap
    the first and third channels up front to keep stdin output colors stable.
    """
    oriented = ImageOps.exif_transpose(img_orig)
    input_image = np.array(oriented)
    if input_image.ndim == 3 and input_image.shape[2] >= 3:
        input_image = input_image.copy()
        input_image[:, :, [0, 2]] = input_image[:, :, [2, 0]]
    return input_image


def read_input_file(input_filename: str | os.PathLike[str]) -> tuple[str | None, ImageArray]:
    """Read one image file into the ndarray form expected by Cropper."""
    try:
        with Image.open(input_filename) as img_orig:
            return img_orig.format, cropper_array_from_pillow_image(img_orig)
    except OSError as exc:
        raise CliError(f"Could not read image file: {input_filename}: {exc}") from exc


def finish_report(
    report: CliReport,
    json_output: str | os.PathLike[str] | None,
    verbose: bool,
    started: float,
) -> int:
    finish_timings(report.timings, started)
    if json_output != "-":
        if report.message:
            print(report.message, file=sys.stderr)
        if verbose:
            print_verbose(report.input, report.output, report.image_format, report.timings)
    try:
        reporting.write(report.to_dict(), json_output)
    except (OSError, TypeError, ValueError) as exc:
        print(f"Could not write JSON diagnostics: {exc}", file=sys.stderr)
        return 1
    return int(report.failure is not None)


def run_crop(
    input_filename: str | None,
    output_filename: str | None,
    stdin: BinaryIO | None,
    stdout: BinaryIO,
    cropper: Cropper,
    json_output: str | os.PathLike[str] | None,
    verbose: bool,
) -> int:
    """Read, crop, and write once; keep transport errors separate from crop data."""
    report = CliReport(input_filename or "stdin", output_filename or "stdout", output_filename)
    report.timings = empty_timings()
    started = time.perf_counter()
    stage = "read"
    try:
        with measure(report.timings, stage):
            if input_filename is None:
                assert stdin is not None  # The stdin wrapper supplies a binary stream.
                input_format, input_image = _read_stdin_image(stdin)
            else:
                input_format, input_image = read_input_file(input_filename)
        stage = "process"
        with measure(report.timings, stage):
            result = cropper.crop(input_image)
        report.crop = result.diagnostics
        if result.image is None:
            report.message = f"No face detected: {report.input}"
        else:
            report.image_format = output_format(input_format, output_filename)
            stage = "write"
            with measure(report.timings, stage):
                if output_filename is None:
                    output_bytes(result.image, stdout, report.image_format)
                else:
                    assert input_filename is not None  # Explicit output is supported only for file input.
                    output(input_filename, output_filename, result.image, image_format=report.image_format)
    except BrokenPipeError:
        report.error = "broken_pipe"
    except (CliError, OSError, ValueError) as exc:
        report.error, report.message = f"{stage}_error", str(exc)
    return finish_report(report, json_output, verbose, started)


def crop_file_to_output(
    input_filename: str | os.PathLike[str],
    output_filename: str | os.PathLike[str] | None = None,
    fheight: int = 500,
    fwidth: int = 500,
    face_percent: int = 50,
    resize: bool = True,
    stdout: BinaryIO | None = None,
    verbose: bool = False,
    json_output: str | os.PathLike[str] | None = None,
) -> int:
    """Crop one image file to a file path or stdout."""
    input_filename = os.fspath(input_filename)
    output_filename = os.fspath(output_filename) if output_filename is not None else None
    stdout = stdout or sys.stdout.buffer
    try:
        reporting.validate_destination(
            json_output,
            input_filename,
            output_filename,
            image_streams=(stdout,) if output_filename is None else (),
        )
        cropper = Cropper(width=fwidth, height=fheight, face_percent=face_percent, resize=resize)
    except ValueError as exc:
        reporting.report_error(exc, json_output)
        return 2
    return run_crop(input_filename, output_filename, None, stdout, cropper, json_output, verbose)


def _read_stdin_image(stdin: BinaryIO) -> tuple[str | None, ImageArray]:
    image_bytes = stdin.read()
    if not image_bytes:
        raise CliError("No image bytes received on stdin")
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            return image.format, cropper_array_from_pillow_image(image)
    except OSError as exc:
        raise CliError(f"Could not read image from stdin: {exc}") from exc


def crop_stdin_to_stdout(
    stdin: BinaryIO | None = None,
    stdout: BinaryIO | None = None,
    fheight: int = 500,
    fwidth: int = 500,
    face_percent: int = 50,
    resize: bool = True,
    verbose: bool = False,
    json_output: str | os.PathLike[str] | None = None,
) -> int:
    """Read image bytes from stdin, crop, and write image bytes to stdout."""
    stdin = stdin or sys.stdin.buffer
    stdout = stdout or sys.stdout.buffer
    try:
        reporting.validate_destination(json_output, image_streams=(stdin, stdout))
        cropper = Cropper(width=fwidth, height=fheight, face_percent=face_percent, resize=resize)
    except ValueError as exc:
        reporting.report_error(exc, json_output)
        return 2
    return run_crop(None, None, stdin, stdout, cropper, json_output, verbose)


class CliArguments(argparse.Namespace):
    source: str | None
    output: str | None
    width: int
    height: int
    facePercent: int
    no_resize: bool
    verbose: bool
    json_output: str | None


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args: Any, json_stderr: bool = False, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.json_stderr = json_stderr

    def error(self, message: str) -> NoReturn:
        if self.json_stderr:
            reporting.report_error(message, "-")
            self.exit(2)
        super().error(message)


def _json_stderr(args: list[str]) -> bool:
    options = args[: args.index("--")] if "--" in args else args
    return "--json=-" in options or any(
        arg == "--json" and i + 1 < len(options) and options[i + 1] == "-" for i, arg in enumerate(options)
    )


def parse_args(args: list[str]) -> CliArguments:
    """Helper function. Parses the arguments given to the CLI."""
    help_d = {
        "desc": "Automatically crops faces from pictures",
        "source": "Image file, or '-' to read image bytes from stdin.",
        "output": """Output file, or output directory for a single input image.
                      If omitted, cropped image bytes are written to stdout.""",
        "width": "Width of cropped files in px. Default=500",
        "height": "Height of cropped files in px. Default=500",
        "facePercent": "Percentage of face to image height",
        "no_resize": """Do not resize images to the specified width and height,
                      but instead use the original image's pixels.""",
        "verbose": "Write timings and basic processing details to stderr",
        "json": "Write JSON crop diagnostics to a file, or to stderr with '-'",
    }

    parser = ArgumentParser(description=help_d["desc"], json_stderr=_json_stderr(args), allow_abbrev=False)
    parser.add_argument(
        "source",
        nargs="?",
        type=input_path,
        help=help_d["source"],
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s version {}".format(__version__),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help=help_d["verbose"],
    )
    parser.add_argument(
        "-n",
        "--no-resize",
        action="store_true",
        help=help_d["no_resize"],
    )
    parser.add_argument(
        "-o",
        "--output",
        "-p",
        "--path",
        default=None,
        help=help_d["output"],
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        default=None,
        metavar="PATH",
        help=help_d["json"],
    )
    parser.add_argument("-w", "--width", type=size, default=500, help=help_d["width"])
    parser.add_argument("-H", "--height", type=size, default=500, help=help_d["height"])
    parser.add_argument("--facePercent", type=size, default=50, help=help_d["facePercent"])
    parsed = CliArguments()
    parser.parse_args(args, namespace=parsed)
    return parsed


def resolve_file_output(input_source: str, output_arg: str | None) -> str | None:
    """Resolve --output for single-image mode."""
    if output_arg is None:
        return None
    output_ext = os.path.splitext(output_arg)[1]
    if os.path.isdir(output_arg) or not output_ext:
        os.makedirs(output_arg, exist_ok=True)
        output_filename = os.path.join(output_arg, os.path.basename(input_source))
        return validate_output_extension(output_filename)

    output_dir = os.path.dirname(os.path.abspath(output_arg))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    return validate_output_extension(os.path.abspath(output_arg))


def run_single_file_mode(args: CliArguments, input_source: str, resize: bool) -> int:
    """Run single-image file mode."""
    output_filename = resolve_file_output(input_source, args.output)
    return crop_file_to_output(
        input_source,
        output_filename,
        args.height,
        args.width,
        args.facePercent,
        resize,
        verbose=args.verbose,
        json_output=args.json_output,
    )


def command_line_interface() -> NoReturn:
    """
    AUTOCROP
    --------
    Crops faces from image files or stdin.
    """
    args = parse_args(sys.argv[1:])
    input_source = args.source
    if input_source is None:
        if sys.stdin.isatty():
            message = "autocrop: an input image or '-' is required"
            if args.json_output == "-":
                reporting.report_error(message, "-")
                raise SystemExit(2)
            raise SystemExit(message)
        input_source = "-"

    resize = not args.no_resize

    if input_source == "-":
        status = crop_stdin_to_stdout(
            fheight=args.height,
            fwidth=args.width,
            face_percent=args.facePercent,
            resize=resize,
            verbose=args.verbose,
            json_output=args.json_output,
        )
        sys.exit(status)

    try:
        status = run_single_file_mode(args, input_source, resize)
    except (CliError, OSError) as exc:
        reporting.report_error(exc, args.json_output)
        status = 2
    sys.exit(status)
