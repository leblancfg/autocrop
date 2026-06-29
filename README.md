# autocrop

<p align="center">
  <img src="docs/assets/social-preview.svg" alt="autocrop: crop images around faces from Python or the shell" width="760">
</p>

[![CI](https://github.com/leblancfg/autocrop/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/leblancfg/autocrop/actions/workflows/ci.yml) [![Documentation](https://img.shields.io/badge/docs-passing-success.svg)](https://leblancfg.com/autocrop) [![PyPI version](https://badge.fury.io/py/autocrop.svg)](https://badge.fury.io/py/autocrop) [![Downloads](https://pepy.tech/badge/autocrop)](https://pepy.tech/project/autocrop)

<p align="center"><img title="obama_crop" src="https://cloud.githubusercontent.com/assets/15659410/10975709/3e38de48-83b6-11e5-8885-d95da758ca17.png"></p>

Perfect for profile picture processing for your website or batch work for ID cards, autocrop will output images centered around the biggest face detected.

Docs site draft: the proposed documentation refresh lives in `docs/`.

# Installation
Simple!

~~~sh
pip install autocrop
~~~

# Use
Autocrop can be used [from the command line](#from-the-command-line) or directly [from Python API](#from-python).

## From Python
Import the `Cropper` class, set some parameters (optional), and start cropping.

The `crop` method accepts filepaths or `np.ndarray`, and returns Numpy arrays. These are easily handled with [PIL](https://pillow.readthedocs.io/) or [Matplotlib](https://matplotlib.org/).

~~~python
from PIL import Image
from autocrop import Cropper

cropper = Cropper()

# Get a Numpy array of the cropped image
cropped_array = cropper.crop('portrait.png')

# Save the cropped image with PIL if a face was detected:
if cropped_array is not None:
    cropped_image = Image.fromarray(cropped_array)
    cropped_image.save('cropped.png')
~~~

Haar cascade detection remains the default detector. YuNet can be selected when
you want OpenCV's neural-network face detector:

~~~python
cropper = Cropper(detector="yunet")
~~~

Further examples and use cases are found in the [accompanying Jupyter Notebook](https://github.com/leblancfg/autocrop/blob/master/examples/visual_tests.ipynb).

## From the command line

    usage: autocrop [-h] [-v] [--no-confirm] [-n] [-i INPUT] [-o OUTPUT] [-r REJECT] [-w WIDTH] [-H HEIGHT] [--facePercent FACEPERCENT]
                    [-e EXTENSION] [--detector {haar,yunet}]
                    [source]

    Automatically crops faces from pictures

    options:
      source                Image file, image directory, or '-' to read image bytes from stdin. Directory input requires --output.
      -h, --help            Show this help message and exit
      -v, --version         Show program's version number and exit
      --no-confirm, --skip-prompt
                            Bypass any confirmation prompts
      -n, --no-resize       Do not resize images to the specified width and height, but instead use the original image's pixels.
      -i, --input INPUT
                            Image file or folder where images to crop are located. Use '-' to read image bytes from stdin.
      -o, -p, --output, --path OUTPUT
                            Output file for a single input image, or output directory for directory input. If omitted for a single image,
                            cropped image bytes are written to stdout.
      -r, --reject REJECT
                            Folder where images that could not be cropped will be moved to in directory mode.
      -w, --width WIDTH
                            Width of cropped files in px. Default=500
      -H, --height HEIGHT
                            Height of cropped files in px. Default=500
      --facePercent FACEPERCENT
                            Percentage of face to image height
      -e, --extension EXTENSION
                            Enter the image extension which to save at output
      --detector {haar,yunet}
                            Face detector backend to use

### Examples

* Crop one image and write the cropped image bytes to stdout:
    - `autocrop portrait.jpg > cropped.jpg`
* Crop image bytes from stdin. This uses `-` instead of `--` because `--` is already argparse's standard option terminator:
    - `cat portrait.jpg | autocrop - > cropped.jpg`
    - `autocrop -- > cropped.jpg < portrait.jpg`
* Crop one image and write to an explicit output file:
    - `autocrop portrait.jpg -o cropped.jpg`
* Crop one image and write into an explicit output directory:
    - `autocrop portrait.jpg -o crop`
* Crop every image in the `pics` folder, resize them to 400 px squares, and output them in the `crop` directory:
	- `autocrop -i pics -o crop -w 400 -H 400`.
	- Images where a face can't be detected will be left in `crop`.
* Same as above, but output the images with undetected faces to the `reject` directory:
	- `autocrop -i pics -o crop -r reject -w 400 -H 400`.
* Same as above but the image extension will be `png`:
	- `autocrop -i pics -o crop -w 400 -H 400 -e png`
* Crop every image in the `pics` folder and output to the `crop` directory, but keep the original pixels from the images:
    - `autocrop -i pics -o crop --no-resize`
* Use YuNet instead of Haar cascade face detection:
    - `autocrop -i pics -o crop --detector yunet`

Directory input now requires an explicit output directory. For recursive or filtered batch workflows, compose `autocrop` with shell tools instead of relying on implicit whole-folder behavior. Successful single-image and stdin runs are quiet except for cropped image bytes on stdout; diagnostics are written to stderr.

```sh
mkdir -p crop
find pics -type f \( -iname '*.jpg' -o -iname '*.png' \) -print0 |
  while IFS= read -r -d '' file; do
    out="crop/${file#pics/}"
    mkdir -p "$(dirname "$out")"
    autocrop "$file" --detector yunet -e jpg > "${out%.*}.jpg"
  done
```

With [`fd`](https://github.com/sharkdp/fd):

```sh
fd -e jpg -e png . pics -x sh -c 'out="crop/${1#pics/}"; mkdir -p "$(dirname "$out")"; autocrop "$1" --detector yunet -e jpg > "${out%.*}.jpg"' sh {}
```

With `xargs`:

```sh
find pics -type f \( -iname '*.jpg' -o -iname '*.png' \) -print0 |
  xargs -0 -I{} sh -c 'out="crop/${1#pics/}"; mkdir -p "$(dirname "$out")"; autocrop "$1" --detector yunet > "$out"' sh {}
```

With GNU `parallel`:

```sh
find pics -type f \( -iname '*.jpg' -o -iname '*.png' \) -print0 |
  parallel -0 'out="crop/{= s:^pics/:: =}"; mkdir -p "$(dirname "$out")"; autocrop {} --detector yunet > "$out"'
```

Explicit in-place directory output remains available by passing the same input and output directory, and still prompts unless `--no-confirm` is used:

```sh
autocrop -i pics -o pics
```

### Detecting faces from video files
You can use autocrop to detect faces in frames extracted from a video. A great way to [perform the frame extraction step is with `ffmpeg`](https://ffmpeg.org/download.html):

```sh
mkdir frames faces

# Extract one frame per second
ffmpeg -i input.mp4 -filter:v fps=fps=1/60 frames/ffmpeg_%0d.bmp

# Crop faces as jpg
autocrop -i frames -o faces -e jpg
```


# Supported file types

The following file types are supported:

- EPS files (`.eps`)
- GIF files (`.gif`) (only the first frame of an animated GIF is used)
- JPEG 2000 files (`.j2k`, `.j2p`, `.jp2`, `.jpx`)
- JPEG files (`.jpeg`, `.jpg`, `.jpe`)
- LabEye IM files (`.im`)
- macOS ICNS files (`.icns`)
- Microsoft Paint bitmap files (`.msp`)
- PCX files (`.pcx`)
- Portable Network Graphics (`.png`)
- Portable Pixmap files (`.pbm`, `.pgm`, `.ppm`)
- SGI files (`.sgi`)
- SPIDER files (`.spi`)
- TGA files (`.tga`)
- TIFF files (`.tif`, `.tiff`)
- WebP (`.webp`)
- Windows bitmap files (`.bmp`, `.dib`)
- Windows ICO files (`.ico`)
- X bitmap files (`.xbm`)

# Misc
### Installing directly
In some cases, you may wish the package directly, instead of through [PyPI](https://pypi.python.org/pypi):

~~~
cd ~
git clone https://github.com/leblancfg/autocrop
cd autocrop
uv sync
~~~

### Development environment
Best practice for your projects is of course to use virtual environments. For
local development, autocrop uses [uv](https://docs.astral.sh/uv/):

~~~sh
uv sync
uv run autocrop --help
~~~

Autocrop is [currently being tested on](https://github.com/leblancfg/autocrop/actions/workflows/ci.yml):

* Python 3.10 to 3.14
* OS:
    - Linux
    - macOS
    - Windows

# More Info
Check out:

* http://docs.opencv.org/master/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0
* http://docs.opencv.org/master/d5/daf/tutorial_py_histogram_equalization.html#gsc.tab=0

Adapted from:

* http://photo.stackexchange.com/questions/60411/how-can-i-batch-crop-based-on-face-location

### Bundled detector models

Autocrop vendors OpenCV Zoo's `face_detection_yunet_2023mar.onnx` so YuNet works
offline and CI does not depend on runtime downloads. The model source is
`opencv/opencv_zoo`, and OpenCV's model card notes that files in the
`models/face_detection_yunet` directory are MIT licensed.

### Contributing

Although autocrop is essentially a CLI wrapper around a single OpenCV function, it is actively developed. It has active users throughout the world.

If you would like to contribute, please consult the [contribution docs](CONTRIBUTING.md).
