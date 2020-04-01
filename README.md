# autocrop

[![Travis Status](https://travis-ci.org/leblancfg/autocrop.svg?branch=master)](https://travis-ci.org/leblancfg/autocrop) [![AppVeyor Build Status](https://ci.appveyor.com/api/projects/status/y2iqfj2vgt6pofn3/branch/master?svg=true)](https://ci.appveyor.com/project/leblancfg/autocrop/branch/master) [![codecov](https://codecov.io/gh/leblancfg/autocrop/branch/master/graph/badge.svg)](https://codecov.io/gh/leblancfg/autocrop) [![Documentation](https://img.shields.io/badge/docs-passing-success.svg)](https://leblancfg.com/autocrop) [![PyPI version](https://badge.fury.io/py/autocrop.svg)](https://badge.fury.io/py/autocrop) [![Downloads](https://pepy.tech/badge/autocrop)](https://pepy.tech/project/autocrop) [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/leblancfg/autocrop.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/leblancfg/autocrop/context:python)

<p align="center"><img title="obama_crop" src="https://cloud.githubusercontent.com/assets/15659410/10975709/3e38de48-83b6-11e5-8885-d95da758ca17.png"></p>

Perfect for profile picture processing for your website or batch work for ID cards, autocrop will output images centered around the biggest face detected.

## Installation
Simple!

~~~sh
pip install autocrop
~~~

## Use
Autocrop can be used [from the command line](#from-the-command-line) or directly [from Python API](#from-python).

### From the command line

	usage: [-h] [-o OUTPUT] [-i INPUT] [-w WIDTH] [-H HEIGHT] [-v]

	Automatically crops faces from batches of pictures

	optional arguments:
	  -h, --help
	  		Show this help message and exit
	  -o, --output, -p, --path
			Folder where cropped images will be placed.
			Default: current working directory
	  -r, --reject
			Folder where images without detected faces will be placed.
			Default: same as output directory
	  -i, --input
			Folder where images to crop are located.
			Default: current working directory
	  -w, --width
			Width of cropped files in px. Default=500
	  -H, --height
			Height of cropped files in px. Default=500
	  --facePercent
	  		Zoom factor. Percentage of face height to image height.
	  -v, --version
	  		Show program's version number and exit

#### Examples

* Crop every image in the `pics` folder, resize them to 400 px squares, and output them in the `crop` directory:
	- `autocrop -i pics -o crop -w 400 -H 400`.
	- Images where a face can't be detected will be left in `crop`.
* Same as above, but output the images with undetected faces to the `reject` folder:
	- `autocrop -i pics -o crop -r reject -w 400 -H 400`.
	
If no output folder is added, asks for confirmation and destructively crops images in-place.

### From Python
Import the `Cropper` class, set some parameters (optional), and start cropping.

The `crop` method accepts filepaths or `np.ndarray`, and returns Numpy arrays. These are easily handled with [PIL](https://pillow.readthedocs.io/) or [Matplotlib](https://matplotlib.org/).

~~~python
from PIL import Image
from autocrop import Cropper

cropper = Cropper()

# Get a Numpy array of the cropped image
cropped_array = cropper.crop('portrait.png')

# Save the cropped image with PIL
cropped_image = Image.fromarray(cropped_array)
cropped_image.save('cropped.png')
~~~

Further examples and use cases are found in the [accompanying Jupyter Notebook](https://github.com/leblancfg/autocrop/blob/master/tests/visual_tests.ipynb).

## Supported file types

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


### Gotchas
Autocrop uses OpenCV to perform face detection, which is installed through binary [wheels](http://pythonwheels.com/). If you *already* have OpenCV 3+ installed, you may wish to uninstall the additional OpenCV installation: `pip uninstall opencv-python`.

### Installing directly
In some cases, you may wish the package directly, instead of through [PyPI](https://pypi.python.org/pypi):

~~~
cd ~
git clone https://github.com/leblancfg/autocrop
cd autocrop
pip install .
~~~

### conda
Development of a `conda-forge` package for the [Anaconda Python distribution](https://www.anaconda.com/download/) is also currently slated for development. Please leave feedback on [issue #7](https://github.com/leblancfg/autocrop/issues/7) if you are insterested in helping out.

## Requirements
Best practice for your projects is of course to [use virtual environments](http://docs.python-guide.org/en/latest/dev/virtualenvs/). At the very least, you will need to [have pip installed](https://pip.pypa.io/en/stable/installing/).

Autocrop is currently being tested on:

* Python 3.5+
* OS:
    - Linux
    - macOS
    - Windows

## More Info
Check out:

* http://docs.opencv.org/master/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0
* http://docs.opencv.org/master/d5/daf/tutorial_py_histogram_equalization.html#gsc.tab=0

Adapted from:

* http://photo.stackexchange.com/questions/60411/how-can-i-batch-crop-based-on-face-location

## Contributing

Although autocrop is essentially a CLI wrapper around a single OpenCV function, it is actively developed. It has active users throughout the world.

If you would like to contribute, please consult the [contribution docs](CONTRIBUTING.md).
