# autocrop
[![Travis Build Status](https://img.shields.io/travis/leblancfg/autocrop.svg)](https://travis-ci.org/leblancfg/autocrop) [![AppVeyor Build Status](https://img.shields.io/appveyor/ci/leblancfg/autocrop.svg?label=%22Windows%22)](https://ci.appveyor.com/project/leblancfg/autocrop/branch/master) [![PyPI version](https://badge.fury.io/py/autocrop.svg)](https://badge.fury.io/py/autocrop) 

<p align="center"><img title="obama_crop" src="https://cloud.githubusercontent.com/assets/15659410/10975709/3e38de48-83b6-11e5-8885-d95da758ca17.png"></p>

Perfect for profile picture processing for your website or batch work for ID cards, autocrop will output images centered around the biggest face detected.

## Use
From the command line:

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

* Example: `autocrop -p pics -w 400 -H 400`.

### What it does
The previous command will:
1. Create a copy of all images found in the top level of `pics` to `pics/bkp`,
2. Crop to 400x400 pixels all images found in the top level of `pics` to `pics/crop`.
    
Images where a face can't be detected will be left in `pics`.

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
Pull requests are always welcome. I don't have much time to put into this project as "I've already scratched my own itch", but realize it can be useful to larger community. If you'd like to contribute to the codebase:

1. Fork the repository on GitHub and clone it on your local machine,
    * `git clone https://github.com/your_username/autocrop`
2. Make a branch off of master and make the changes you have in mind,
    * `git checkout -b issue-007`
3. Run the tests with `pytest` in the root-level directory to make sure you didn't mistakenly break anything else.
4. Commit your changes: one item per commit if possible,
    * `git commit -a -m 'fixed issue 007'`
5. Once development is done, always run `flake8 .` to check your coding style, as [PEP8 is enforced and will fail your CI](https://www.caktusgroup.com/blog/2015/08/15/making-clean-code-part-your-build-process/) otherwise.
6. Push the modified codebase back to your forked version on Github,
    * `git push origin issue-007`
7. On GitHub, submit a Pull Request to the master branch.

If you'd like to have a development environment for autocrop, you should create a virtualenv and then do `pip install -e .` from within the directory.
