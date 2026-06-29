import argparse
import io
import os
import shutil
import stat
import sys
import time

import numpy as np
from PIL import Image

from . import _timing
from .__version__ import __version__
from .autocrop import Cropper
from .constants import IMAGE_FORMATS_BY_EXTENSION, INPUT_FILETYPES


def _preserve_metadata(input_filename, output_filename, source_stat):
    """Preserve safe filesystem metadata from the source image."""
    if input_filename != output_filename:
        shutil.copystat(input_filename, output_filename)
    os.chmod(output_filename, stat.S_IMODE(source_stat.st_mode))
    os.utime(
        output_filename,
        ns=(source_stat.st_atime_ns, source_stat.st_mtime_ns),
    )


def _image_save_kwargs(input_filename):
    """Return image metadata Pillow can preserve while writing the crop."""
    save_kwargs = {}
    with Image.open(input_filename) as img_orig:
        if "exif" in img_orig.info:
            save_kwargs["exif"] = img_orig.info["exif"]
        if "icc_profile" in img_orig.info:
            save_kwargs["icc_profile"] = img_orig.info["icc_profile"]
    return save_kwargs


def output(input_filename, output_filename, image, source_stat=None):
    """Write cropped image data to an output file."""
    if source_stat is None:
        source_stat = os.stat(input_filename)
    if input_filename != output_filename:
        shutil.copy(input_filename, output_filename)
    save_kwargs = _image_save_kwargs(input_filename)
    img_new = Image.fromarray(image)
    img_new.save(output_filename, **save_kwargs)
    _preserve_metadata(input_filename, output_filename, source_stat)


def output_bytes(image, output_stream, image_format):
    """Write cropped image bytes to a binary stream."""
    img_new = Image.fromarray(image)
    img_new.save(output_stream, format=image_format)


def input_path(p):
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


def size(i):
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


def chk_extension(extension):
    """Check if the extension passed is valid or not."""
    error = "Invalid image extension"
    extension = str(extension).lower()
    if not extension.startswith("."):
        extension = f".{extension}"
    if extension in INPUT_FILETYPES:
        return extension.replace(".", "")
    else:
        raise argparse.ArgumentTypeError(error)


def output_format(input_format=None, extension=None):
    """Return a Pillow format name for stream or file output."""
    if extension:
        return IMAGE_FORMATS_BY_EXTENSION[f".{extension}"]
    return input_format or "PNG"


def empty_timings():
    """Return a timing map with stable keys for verbose output."""
    return {
        "imports": _timing.import_seconds(),
        "read": 0.0,
        "process": 0.0,
        "write": 0.0,
        "total": 0.0,
    }


def timed_step(timings, key, callback):
    """Run callback and add elapsed seconds to a timing key."""
    started = time.perf_counter()
    try:
        return callback()
    finally:
        timings[key] += time.perf_counter() - started


def finish_timings(timings, started):
    """Set total time, including package imports and command runtime."""
    timings["total"] = timings["imports"] + time.perf_counter() - started


def print_verbose(input_label, output_label, image_format, timings):
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


def crop_image(
    path_or_array,
    image_format,
    extension,
    fheight,
    fwidth,
    face_percent,
    resize,
):
    """Crop a single image path or numpy array."""
    cropper = Cropper(
        width=fwidth,
        height=fheight,
        face_percent=face_percent,
        resize=resize,
    )
    image = cropper.crop(path_or_array)
    if image is None:
        return None, None
    return image, output_format(image_format, extension)


def cropper_array_from_pillow_image(img_orig):
    """
    Return an array in the color-channel order expected by Cropper.crop(np.ndarray).

    Cropper treats ndarray inputs as OpenCV-style BGR/BGRA and converts them back
    to RGB/RGBA before returning. Pillow decodes stream input as RGB/RGBA, so swap
    the first and third channels up front to keep stdin output colors stable.
    """
    input_image = np.array(img_orig)
    if input_image.ndim == 3 and input_image.shape[2] >= 3:
        input_image = input_image.copy()
        input_image[:, :, [0, 2]] = input_image[:, :, [2, 0]]
    return input_image


def read_input_file(input_filename):
    """Read one image file into the ndarray form expected by Cropper."""
    with Image.open(input_filename) as img_orig:
        return img_orig.format, cropper_array_from_pillow_image(img_orig)


def crop_file_to_output(
    input_filename,
    output_filename=None,
    extension=None,
    fheight=500,
    fwidth=500,
    face_percent=50,
    resize=True,
    stdout=None,
    verbose=False,
):
    """Crop one image file to a file path or stdout."""
    timings = empty_timings()
    started = time.perf_counter()
    image_format = None
    output_label = output_filename or "stdout"

    try:
        input_format, input_image = timed_step(
            timings, "read", lambda: read_input_file(input_filename)
        )
        image, image_format = timed_step(
            timings,
            "process",
            lambda: crop_image(
                input_image,
                input_format,
                extension,
                fheight,
                fwidth,
                face_percent,
                resize,
            ),
        )
        if image is None:
            print(f"No face detected: {input_filename}", file=sys.stderr)
            return 1

        if output_filename is None:
            timed_step(
                timings,
                "write",
                lambda: output_bytes(image, stdout or sys.stdout.buffer, image_format),
            )
        else:
            timed_step(
                timings,
                "write",
                lambda: output(input_filename, output_filename, image),
            )
        return 0
    finally:
        finish_timings(timings, started)
        if verbose:
            print_verbose(input_filename, output_label, image_format, timings)


def crop_stdin_to_stdout(
    stdin=None,
    stdout=None,
    extension=None,
    fheight=500,
    fwidth=500,
    face_percent=50,
    resize=True,
    verbose=False,
):
    """Read image bytes from stdin, crop, and write image bytes to stdout."""
    stdin = stdin or sys.stdin.buffer
    stdout = stdout or sys.stdout.buffer
    timings = empty_timings()
    started = time.perf_counter()
    image_format = None

    try:

        def read_stdin_image():
            image_bytes = stdin.read()
            if not image_bytes:
                return None, None, "No image bytes received on stdin"
            try:
                with Image.open(io.BytesIO(image_bytes)) as img_orig:
                    return (
                        img_orig.format,
                        cropper_array_from_pillow_image(img_orig),
                        None,
                    )
            except OSError as exc:
                return None, None, f"Could not read image from stdin: {exc}"

        input_format, input_image, read_error = timed_step(
            timings, "read", read_stdin_image
        )
        if read_error:
            print(read_error, file=sys.stderr)
            return 1

        image, image_format = timed_step(
            timings,
            "process",
            lambda: crop_image(
                input_image,
                input_format,
                extension,
                fheight,
                fwidth,
                face_percent,
                resize,
            ),
        )
        if image is None:
            print("No face detected on stdin image", file=sys.stderr)
            return 1
        timed_step(timings, "write", lambda: output_bytes(image, stdout, image_format))
        return 0
    finally:
        finish_timings(timings, started)
        if verbose:
            print_verbose("stdin", "stdout", image_format, timings)


def parse_args(args):
    """Helper function. Parses the arguments given to the CLI."""
    help_d = {
        "desc": "Automatically crops faces from pictures",
        "source": "Image file, or '-' to read image bytes from stdin.",
        "output": """Output file, or output directory for a single input image.
                      If omitted, cropped image bytes are written to stdout.""",
        "extension": "Enter the image extension which to save at output",
        "width": "Width of cropped files in px. Default=500",
        "height": "Height of cropped files in px. Default=500",
        "facePercent": "Percentage of face to image height",
        "no_resize": """Do not resize images to the specified width and height,
                      but instead use the original image's pixels.""",
        "verbose": "Write timings and basic processing details to stderr",
    }

    parser = argparse.ArgumentParser(description=help_d["desc"])
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
    parser.add_argument("-w", "--width", type=size, default=500, help=help_d["width"])
    parser.add_argument("-H", "--height", type=size, default=500, help=help_d["height"])
    parser.add_argument(
        "--facePercent", type=size, default=50, help=help_d["facePercent"]
    )
    parser.add_argument(
        "-e", "--extension", type=chk_extension, default=None, help=help_d["extension"]
    )
    return parser.parse_args(args)


def resolve_file_output(input_source, output_arg, extension):
    """Resolve --output for single-image mode."""
    if output_arg is None:
        return None
    output_ext = os.path.splitext(output_arg)[1]
    if os.path.isdir(output_arg) or not output_ext:
        os.makedirs(output_arg, exist_ok=True)
        basename = os.path.basename(input_source)
        if extension:
            basename = os.path.splitext(basename)[0] + "." + extension
        return os.path.join(output_arg, basename)

    output_dir = os.path.dirname(os.path.abspath(output_arg))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    return os.path.abspath(output_arg)


def run_single_file_mode(args, input_source, resize):
    """Run single-image file mode."""
    output_filename = resolve_file_output(input_source, args.output, args.extension)
    return crop_file_to_output(
        input_source,
        output_filename,
        args.extension,
        args.height,
        args.width,
        args.facePercent,
        resize,
        verbose=args.verbose,
    )


def command_line_interface():
    """
    AUTOCROP
    --------
    Crops faces from image files or stdin.
    """
    args = parse_args(sys.argv[1:])
    input_source = args.source
    if input_source is None:
        if sys.stdin.isatty():
            raise SystemExit("autocrop: an input image or '-' is required")
        input_source = "-"

    resize = not args.no_resize

    if input_source == "-":
        status = crop_stdin_to_stdout(
            extension=args.extension,
            fheight=args.height,
            fwidth=args.width,
            face_percent=args.facePercent,
            resize=resize,
            verbose=args.verbose,
        )
        sys.exit(status)

    status = run_single_file_mode(args, input_source, resize)
    sys.exit(status)
