# autocrop

![obama_crop](https://cloud.githubusercontent.com/assets/15659410/10975709/3e38de48-83b6-11e5-8885-d95da758ca17.png)

Basic Python 2.7 script using openCV, that automatically crops faces from batches of photos.

Perfect for batch work for ID cards or profile pictures, will output 500px wide square images, centered around the biggest face detected. It also adds a little bit of brightness equalization with openCV's built-in CLAHE (Contrast Limited Adaptive Histogram Equalization).

## How-to
The script will process all .jpg files in the /photos directory. The cropped files are placed in photos/crop, and originals are moved to photos/bkp.

If it can't find a face in the picture, it'll simply leave it in /photos.

## Versions
The script works on openCV 2.4.9 and python 2.7.10, and has not been tested otherwise.

## More Info
Check out:
* http://docs.opencv.org/master/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0
* http://docs.opencv.org/master/d5/daf/tutorial_py_histogram_equalization.html#gsc.tab=0
