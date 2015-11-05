# autocrop
Basic Python 2.7 script using openCV, that automatically crops faces from batches of photos.

Perfect for batch work for ID cards or profile pictures, will output square images centered around the biggest face detected, and a slight brightness equalization with openCV's built-in CLAHE (Contrast Limited Adaptive Histogram Equalization).

# How-to
The script will process all .jpg files in its directory. The cropped files are placed in subdirectory /crop, and originals are moved to /bkp.

If it can't find a face in the picture, it'll simply leave it in place.

# Versions
The script works on openCV 2.4.9 and python 2.7.10, and has not been tested otherwise.

# More Info
Check out:
* http://docs.opencv.org/master/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0
* http://docs.opencv.org/master/d5/daf/tutorial_py_histogram_equalization.html#gsc.tab=0
