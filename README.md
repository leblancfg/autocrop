# autocrop
[![Travis Build Status](https://img.shields.io/travis/leblancfg/autocrop.svg)](https://travis-ci.org/leblancfg/autocrop) [![AppVeyor Build Status](https://img.shields.io/appveyor/ci/leblancfg/autocrop.svg?label=%22Windows%22)](https://ci.appveyor.com/project/leblancfg/autocrop/branch/master) [![PyPI version](https://badge.fury.io/py/autocrop.svg)](https://badge.fury.io/py/autocrop) 

<p align="center"><img title="obama_crop" src="https://cloud.githubusercontent.com/assets/15659410/10975709/3e38de48-83b6-11e5-8885-d95da758ca17.png"></p>

Perfect for batch work for ID cards or profile picture processing for your website, autocrop will output images centered around the biggest face detected.

## Use

    usage: autocrop [-h] [-p PATH] [-w WIDTH] [-H HEIGHT] [-v]

    optional arguments:
      -h, --help            show this help message and exit
      -p PATH, --path PATH  folder where images to crop are located. Default:
                            photos/
      -w WIDTH, --width WIDTH
                            width of cropped files in px. Default: 500
      -H HEIGHT, --height HEIGHT
                            height of cropped files in px. Default: 500
      -v, --version         show program's version number and exit

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
