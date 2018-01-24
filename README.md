# autocrop
[![Travis Build Status](https://img.shields.io/travis/leblancfg/autocrop/master.svg)](https://travis-ci.org/leblancfg/autocrop) [![AppVeyor Build Status](https://img.shields.io/appveyor/ci/leblancfg/autocrop/master.svg?label=%22Windows%22)](https://ci.appveyor.com/project/leblancfg/autocrop/branch/master) [![PyPI version](https://badge.fury.io/py/autocrop.svg)](https://badge.fury.io/py/autocrop) 

<p align="center"><img title="obama_crop" src="https://cloud.githubusercontent.com/assets/15659410/10975709/3e38de48-83b6-11e5-8885-d95da758ca17.png"></p>

Perfect for batch work for ID cards or profile picture processing for your website, autocrop will output images centered around the biggest face detected.

## Use
From the command line:

	usage: [-h] [-o OUTPUT] [-i INPUT] [-w WIDTH] [-H HEIGHT] [-v]

	Automatically crops faces from batches of pictures

	optional arguments:
	  -h, --help            Show this help message and exit
	  -o, --output, -p, --path
				Folder where cropped images will be placed.
				Default: current working directory
	  -i, --input
				Folder where images to crop are located.
				Default: current working directory
	  -w, --width
				Width of cropped files in px. Default=500
	  -H, --height
				Height of cropped files in px. Default=500
	  -v, --version         Show program's version number and exit

* Example: `autocrop -i pics -o crop -w 400 -H 400`.

### What it does
The previous command will:
1. Copy all images found in the top level of `pics` to `crop`,
2. Crop around the face and resize to 400x400 pixels all images in `crop`.

Images where a face can't be detected will be left in `crop`.
If no output folder is added, asks for confirmation and destructively crops images in-place.

## Installation
Simple! In your command line, type:

~~~python
pip install autocrop
~~~

### Gotchas
Autocrop uses OpenCV to perform face detection, which is installed through binary [wheels](http://pythonwheels.com/). If you *already* have OpenCV 3+ installed, you may wish to uninstall the additional OpenCV installation: `pip uninstall opencv-python`.

### conda
Development of a `conda-forge` package for the [Anaconda Python distribution](https://www.anaconda.com/download/) is also currently slated for development. Please leave feedback on [issue #7](https://github.com/leblancfg/autocrop/issues/7) if you are insterested in helping out.

### Installing directly
In some cases, you may wish the package directly, instead of through [PyPI](https://pypi.python.org/pypi):

~~~
cd ~
git clone https://github.com/leblancfg/autocrop
cd autocrop
pip install .
~~~

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

We have all the love in the world for extra contributors if you'd like to contribute to the codebase. Please follow these steps:
* Fork the repository on GitHub.
* Install the extra dev packages with `pip install -r requirements-test.txt`
* Make a branch off of master, commit and test your changes to it.

Pull requests are tested on continuous integration (CI) servers before they are green-lit to merge with the master branch.
* Run the tests with `pytest`.
* Always run `flake8 .` before submitting to check your coding style, as your CI will fail otherwise.
* Submit a Pull Request to the master branch on GitHub.

If you have any questions regarding this, please reach me at leblancfg@gmail.com. We'll make sure we get through the steps correctly.

If you'd like to have a development environment for autocrop, you should create a virtualenv and then do `pip install -e .` from within the directory.
