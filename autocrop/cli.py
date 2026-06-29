import argparse
import io
import os
import shutil
import stat
import sys
from typing import Optional

import numpy as np
from PIL import Image

from .__version__ import __version__
from .autocrop import Cropper, ImageReadError
from .constants import (
    QUESTION_OVERWRITE,
    INPUT_FILETYPES,
)


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
    """
    Move the input file to the output location and write over it with the
    cropped image data.
    """
    if source_stat is None:
        source_stat = os.stat(input_filename)
    if input_filename != output_filename:
        # Move the file to the output directory
        shutil.copy(input_filename, output_filename)
    save_kwargs = _image_save_kwargs(input_filename)
    # Encode the image as an in-memory PNG
    img_new = Image.fromarray(image)
    # Write the new image (converting the format to match the output
    # filename if necessary)
    img_new.save(output_filename, **save_kwargs)
    _preserve_metadata(input_filename, output_filename, source_stat)


def output_bytes(image, output_stream, image_format):
    """Write cropped image bytes to a binary stream."""
    img_new = Image.fromarray(image)
    img_new.save(output_stream, format=image_format)


def reject(input_filename, reject_filename, source_stat=None):
    """Move the input file to the reject location."""
    if source_stat is None:
        source_stat = os.stat(input_filename)
    if input_filename != reject_filename:
        # Move the file to the reject directory
        shutil.copy(input_filename, reject_filename)
    _preserve_metadata(input_filename, reject_filename, source_stat)


def status(message, quiet):
    """Write status text to stderr unless quiet mode is enabled."""
    if not quiet:
        print(message, file=sys.stderr)


def main(
    input_d: str,
    output_d: str,
    reject_d: str,
    extension: Optional[str] = None,
    fheight: int = 500,
    fwidth: int = 500,
    facePercent: int = 50,
    resize: bool = True,
    quiet: bool = True,
) -> None:
    """
    Crops folder of images to the desired height and width if a
    face is found.

    If `input_d == output_d` or `output_d is None`, overwrites all files
    where the biggest face was found.

    Parameters:
    -----------

    - `input_d`: `str`
        * Directory to crop images from.
    - `output_d`: `str`
        * Directory where cropped images are placed.
    - `reject_d`: `str`
        * Directory where images that cannot be cropped are placed.
    - `fheight`: `int`, default=`500`
        * Height (px) to which to crop the image.
    - `fwidth`: `int`, default=`500`
        * Width (px) to which to crop the image.
    - `facePercent`: `int`, default=`50`
        * Percentage of face from height.
    - `extension` : `str`
        * Image extension to save at output.
    - `resize`: `bool`, default=`True`
        * If `False`, don't resize the image, but use the original size.

    Side Effects:
    -------------

    - Creates image files in output directory.
    """
    reject_count = 0
    output_count = 0
    input_files = [
        os.path.join(input_d, f)
        for f in os.listdir(input_d)
        if any(f.endswith(t) for t in INPUT_FILETYPES)
    ]
    if output_d is None:
        output_d = input_d
    if reject_d is None and output_d is None:
        reject_d = input_d
    if reject_d is None:
        reject_d = output_d

    # Guard against calling the function directly
    input_count = len(input_files)
    assert input_count > 0

    # Main loop
    cropper = Cropper(
        width=fwidth,
        height=fheight,
        face_percent=facePercent,
        resize=resize,
    )
    for input_filename in input_files:
        basename = os.path.basename(input_filename)
        if extension:
            basename_noext = os.path.splitext(basename)[0]
            output_filename = os.path.join(output_d, basename_noext + "." + extension)
        else:
            output_filename = os.path.join(output_d, basename)
        reject_filename = os.path.join(reject_d, basename)
        image = None
        source_stat = os.stat(input_filename)

        # Attempt the crop
        try:
            image = cropper.crop(input_filename)
        except ImageReadError:
            status("Read error:       {}".format(input_filename), quiet)
            continue

        # Did the crop produce an invalid image?
        if isinstance(image, type(None)):
            reject(input_filename, reject_filename, source_stat)
            status("No face detected: {}".format(reject_filename), quiet)
            reject_count += 1
        else:
            output(input_filename, output_filename, image, source_stat)
            status("Face detected:    {}".format(output_filename), quiet)
            output_count += 1

    # Stop and print status

    status(
        f"{input_count} : Input files, {output_count} : Faces Cropped, {reject_count}",
        quiet,
    )


def input_path(p):
    """Return path, only if input is a valid image file, directory, or stdin."""
    no_folder = "Input path does not exist"
    no_images = "Input folder does not contain any image files"
    no_image_file = "Input file type is not supported"
    if p == "-":
        return p
    p = os.path.abspath(p)
    if not os.path.exists(p):
        raise argparse.ArgumentTypeError(no_folder)
    if os.path.isdir(p):
        filetypes = {os.path.splitext(f)[-1] for f in os.listdir(p)}
        if not any(t in INPUT_FILETYPES for t in filetypes):
            raise argparse.ArgumentTypeError(no_images)
        return p
    if os.path.splitext(p)[-1] not in INPUT_FILETYPES:
        raise argparse.ArgumentTypeError(no_image_file)
    return p


def output_path(p):
    """
    Returns path, if input is a valid directory name.
    If directory doesn't exist, creates it.
    """
    p = os.path.abspath(p)
    if not os.path.isdir(p):
        os.makedirs(p)
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


def compat_input(s=""):  # pragma: no cover
    """Compatibility function to permit testing for Python 2 and 3."""
    try:
        return raw_input(s)
    except NameError:
        # Py2 raw_input() renamed to input() in Py3
        return input(s)  # lgtm[py/use-of-input]


def confirmation(question):
    """Ask a yes/no question via standard input and return the answer."""
    yes_list = ["yes", "y"]
    no_list = ["no", "n"]
    default_str = "[Y]/n"
    prompt_str = "{} {} ".format(question, default_str)

    while True:
        choice = compat_input(prompt_str).lower()

        if not choice:
            return default_str
        if choice in yes_list:
            return True
        if choice in no_list:
            return False

        notification_str = "Please respond with 'y' or 'n'"
        print(notification_str)


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
        "source": """Image file, image directory, or '-' to read image bytes from
                     stdin. Directory input requires --output.""",
        "input": """Image file or folder where images to crop are located.
                     Use '-' to read image bytes from stdin.""",
        "output": """Output file for a single input image, or output directory for
                      directory input. If omitted for a single image, cropped
                      image bytes are written to stdout.""",
        "reject": """Folder where images that could not be cropped will be
                       moved to in directory mode.""",
        "extension": "Enter the image extension which to save at output",
        "width": "Width of cropped files in px. Default=500",
        "height": "Height of cropped files in px. Default=500",
        "y": "Bypass any confirmation prompts",
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
        "--no-confirm",
        "--skip-prompt",
        action="store_true",
        help=help_d["y"],
    )
    parser.add_argument(
        "-n",
        "--no-resize",
        action="store_true",
        help=help_d["no_resize"],
    )
    parser.add_argument(
        "-i", "--input", default=None, type=input_path, help=help_d["input"]
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
        "-r", "--reject", type=output_path, default=None, help=help_d["reject"]
    )
    parser.add_argument("-w", "--width", type=size, default=500, help=help_d["width"])
    parser.add_argument("-H", "--height", type=size, default=500, help=help_d["height"])
    parser.add_argument(
        "--facePercent", type=size, default=50, help=help_d["facePercent"]
    )
    parser.add_argument(
        "-e", "--extension", type=chk_extension, default=None, help=help_d["extension"]
    )
    parsed = parser.parse_args(args)
    if parsed.input is not None and parsed.source is not None:
        parser.error("use either positional source or --input, not both")
    return parsed


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


def run_directory_mode(args, input_source, resize):
    """Run explicit directory batch mode."""
    if args.output is None:
        raise SystemExit(
            "autocrop: directory input requires --output. "
            "Use find/fd to stream files one at a time."
        )

    args.output = output_path(args.output)
    if not args.no_confirm and input_source == args.output:
        if not confirmation(QUESTION_OVERWRITE):
            sys.exit()
    if input_source == args.output:
        args.output = None
    main(
        input_source,
        args.output,
        args.reject,
        args.extension,
        args.height,
        args.width,
        args.facePercent,
        resize,
    )
    return 0


def command_line_interface():
    """
    AUTOCROP
    --------
    Crops faces from batches of images.
    """
    args = parse_args(sys.argv[1:])
    input_source = args.input or args.source
    if input_source is None:
        if sys.stdin.isatty():
            raise SystemExit(
                "autocrop: an input image, input directory, or '-' is required"
            )
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

    if os.path.isfile(input_source):
        status = run_single_file_mode(args, input_source, resize)
        sys.exit(status)

    run_directory_mode(args, input_source, resize)
