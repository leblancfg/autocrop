# autocrop

![obama_crop](https://cloud.githubusercontent.com/assets/15659410/10975709/3e38de48-83b6-11e5-8885-d95da758ca17.png)

Basic script using openCV, that automatically detects and crops faces from batches of photos.

Perfect for batch work for ID cards or profile pictures, will output 500px wide square images, centered around the biggest face detected. It can also add a touch of auto gamma correction.

## Dependencies
### Conda
The easiest way to run *autocrop* is to use the [Anaconda Python distribution](https://www.anaconda.com/download/) and run the following:

    conda install --file requirements.txt

If running on Windows, this is by far the sanest way to approach this problem. Installing Anaconda also doesn't require admin privileges on Windows.

### pip
Otherwise, binaries for the Python-only bindings for OpenCV have recently been made available through pip, which makes installation a breeze.

    pip install numpy opencv-python

## Installation and How-to
Just clone this repo in your shell:

    git clone https://github.com/leblancfg/autocrop

Move your pictures to be cropped in the *photos* directory, then run the script with:

    cd autocrop
    python autocrop.py

Simple!

The script will process all `.jpg` files in the `/photos` directory. The cropped files are placed in `photos/crop`, and originals are moved to `photos/bkp`.

If it can't find a face in the picture, it'll simply leave it in `/photos`.

## Versions
The script works on openCV 2.4.9 and python 2.7+ and 3+. It has not been tested otherwise. For now, it also artificially restricts filetype as jpg and output size as 500px. These values can easily be tweaked in the header in `autocrop.py`.

## More Info
Check out:
* http://docs.opencv.org/master/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0
* http://docs.opencv.org/master/d5/daf/tutorial_py_histogram_equalization.html#gsc.tab=0

Adapted from:
* http://photo.stackexchange.com/questions/60411/how-can-i-batch-crop-based-on-face-location

## TODO
Pull requests welcome!
* Handle input filetypes for *.bmp, *.dib, *.jp2,*.png, *.webp, *.pbm, *.pgm, *.ppm, *.sr, *.ras, *.tiff, *.tif
* Handle output image size.
* Handle CLI input: `$ autocrop [-w width] [-h height] [-i input-folder] [-o output-folder] [--passport=<country>]`
