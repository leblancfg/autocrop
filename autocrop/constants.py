FIXEXP = True  # Flag to fix underexposition
MINFACE = 8  # Minimum face size ratio; too low and we get false positives
INCREMENT = 0.06
GAMMA_THRES = 0.001
GAMMA = 0.90
FACE_RATIO = 6  # Face / padding ratio
QUESTION_OVERWRITE = "Overwrite image files?"

# File types supported by OpenCV
CV2_FILETYPES = [
    ".bmp",
    ".dib",
    ".jp2",
    ".jpe",
    ".jpeg",
    ".jpg",
    ".pbm",
    ".pgm",
    ".png",
    ".ppm",
    ".ras",
    ".sr",
    ".tif",
    ".tiff",
    ".webp",
]

# File types supported by Pillow
PILLOW_FILETYPES = [
    ".eps",
    ".gif",
    ".icns",
    ".ico",
    ".im",
    ".msp",
    ".pcx",
    ".sgi",
    ".spi",
    ".xbm",
]

CASCFILE = "haarcascade_frontalface_default.xml"
