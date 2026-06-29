import argparse
import io
import os
import shutil
import stat
import sys

import numpy as np
from PIL import Image

from .__version__ import __version__
from .autocrop import Cropper
from .constants import INPUT_FILETYPES


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
    if not os.path.isfile(p) or os.path.splitext(p)[-1] not in INPUT_FILETYPES:
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
        return extension.lower().replace(".", "")
    else:
        raise argparse.ArgumentTypeError(error)


def output_format(input_format=None, extension=None):
    """Return a Pillow format name for stream or file output."""
    if extension:
        return Image.registered_extensions()[f".{extension}"]
    return input_format or "PNG"


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


def crop_file_to_output(
    input_filename,
    output_filename=None,
    extension=None,
    fheight=500,
    fwidth=500,
    face_percent=50,
    resize=True,
    stdout=None,
):
    """Crop one image file to a file path or stdout."""
    with Image.open(input_filename) as img_orig:
        input_format = img_orig.format

    image, image_format = crop_image(
        input_filename,
        input_format,
        extension,
        fheight,
        fwidth,
        face_percent,
        resize,
    )
    if image is None:
        print(f"No face detected: {input_filename}", file=sys.stderr)
        return 1

    if output_filename is None:
        output_bytes(image, stdout or sys.stdout.buffer, image_format)
    else:
        output(input_filename, output_filename, image)
    return 0


def crop_stdin_to_stdout(
    stdin=None,
    stdout=None,
    extension=None,
    fheight=500,
    fwidth=500,
    face_percent=50,
    resize=True,
):
    """Read image bytes from stdin, crop, and write image bytes to stdout."""
    stdin = stdin or sys.stdin.buffer
    stdout = stdout or sys.stdout.buffer
    image_bytes = stdin.read()
    if not image_bytes:
        print("No image bytes received on stdin", file=sys.stderr)
        return 1

    try:
        with Image.open(io.BytesIO(image_bytes)) as img_orig:
            input_format = img_orig.format
            input_image = cropper_array_from_pillow_image(img_orig)
    except OSError as exc:
        print(f"Could not read image from stdin: {exc}", file=sys.stderr)
        return 1

    image, image_format = crop_image(
        input_image,
        input_format,
        extension,
        fheight,
        fwidth,
        face_percent,
        resize,
    )
    if image is None:
        print("No face detected on stdin image", file=sys.stderr)
        return 1
    output_bytes(image, stdout, image_format)
    return 0


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
    }

    parser = argparse.ArgumentParser(description=help_d["desc"])
    parser.add_argument(
        "source",
        nargs="?",
        type=input_path,
        help=help_d["source"],
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s version {}".format(__version__),
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
        )
        sys.exit(status)

    status = run_single_file_mode(args, input_source, resize)
    sys.exit(status)
