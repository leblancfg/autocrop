# autocrop
[![Travis Build Status](https://img.shields.io/travis/leblancfg/autocrop/master.svg)](https://travis-ci.org/leblancfg/autocrop) [![AppVeyor Build Status](https://img.shields.io/appveyor/ci/leblancfg/autocrop/master.svg?label=%22Windows%22)](https://ci.appveyor.com/project/leblancfg/autocrop/branch/master) [![Codecov master](https://img.shields.io/codecov/c/github/leblancfg/autocrop/master.svg)](https://codecov.io/gh/leblancfg/autocrop) [![PyPI version](https://badge.fury.io/py/autocrop.svg)](https://badge.fury.io/py/autocrop) [![Downloads](https://pepy.tech/badge/autocrop)](https://pepy.tech/project/autocrop) [![Known Vulnerabilities](https://snyk.io/test/github/leblancfg/autocrop/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/leblancfg/autocrop?targetFile=requirements.txt) [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/leblancfg/autocrop.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/leblancfg/autocrop/context:python)

<p align="center"><img title="obama_crop" src="https://cloud.githubusercontent.com/assets/15659410/10975709/3e38de48-83b6-11e5-8885-d95da758ca17.png"></p>

Perfect for profile picture processing for your website or batch work for ID cards, autocrop will output images centered around the biggest face detected.

## Use
From the command line:

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
	  		Percentage of Face height to image height (zoom factor)
	  --padUp
	  		Padding up value compared to padDown. Default=50
	  --padDown
	  		Padding down value compared to padDown. Default=50
	  --padLeft
	  		Padding left value compared to padRight. Default=50
	  --padRight
	  		Padding right value compared to padLeft. Default=50
	  -v, --version
	  		Show program's version number and exit


### Examples

* Crop every image in the `pics` folder, resize them to 400 px squares, and output them in the `crop` directory:
	- `autocrop -i pics -o crop -w 400 -H 400`.
	- Images where a face can't be detected will be left in `crop`.
* Same as above, but output the images with undetected faces to the `reject` folder:
	- `autocrop -i pics -o crop -r nofaces -w 400 -H 400`.
* Same as the first example, but add more padding at the bottom:
	- `autocrop -i pics -o crop -w 400 -H 400 --facePercent 50 --padUp 20 --padDown 50`.
	
If no output folder is added, asks for confirmation and destructively crops images in-place.

### Supported file types

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

## Installation
Simple! In your command line, type:

~~~python
pip install autocrop
~~~

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
* Python:
    - 2.7
    - 3.4
    - 3.5
    - 3.6
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
