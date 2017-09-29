# autocrop [![Build Status](https://travis-ci.org/leblancfg/autocrop.svg?branch=master)](https://travis-ci.org/leblancfg/autocrop) 

<p align="center"><img title="obama_crop" src="https://cloud.githubusercontent.com/assets/15659410/10975709/3e38de48-83b6-11e5-8885-d95da758ca17.png"></p>

Basic script using openCV, that automatically detects and crops faces from batches of photos.

Perfect for batch work for ID cards or profile pictures, will output images centered around the biggest face detected. It can also add a touch of auto gamma correction.

## Installation
>**N.B. 28/019/2017**: `pip install autocrop` should now work on most platforms, as well as a basic command-line interface (CLI). Testing on further platforms is currently under way. If this fails:

The script will process all `.jpg` files in the `/photos` directory. The cropped files are placed in `photos/crop`, and originals are moved to `photos/bkp`.

If it can't find a face in the picture, it'll simply leave it in `/photos`.

### conda
The easiest way to run *autocrop* is to use the [Anaconda Python distribution](https://www.anaconda.com/download/) and run the following:

    git clone https://github.com/leblancfg/autocrop
    conda install --channel conda-forge --file requirements.txt
    
Move your pictures to be cropped in the *photos* directory, then run the script with:

    cd autocrop
    python autocrop.py
    
If running on Windows, this is by far the sanest way to approach this problem. Also, installing Anaconda doesn't require admin privileges on Windows.

### pip
Otherwise, binaries for the Python-only bindings for OpenCV have recently been made available through pip, which makes installation a breeze.

    git clone https://github.com/leblancfg/autocrop
    pip install numpy opencv-python
    
Move your pictures to be cropped in the *photos* directory, then run the script with:

    cd autocrop
    python autocrop.py

## Requirements
The script works on Python 2.7 and 3+, and on Windows, macOS and Linux. It has not been tested otherwise.

## More Info
Check out:
* http://docs.opencv.org/master/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0
* http://docs.opencv.org/master/d5/daf/tutorial_py_histogram_equalization.html#gsc.tab=0

Adapted from:
* http://photo.stackexchange.com/questions/60411/how-can-i-batch-crop-based-on-face-location
