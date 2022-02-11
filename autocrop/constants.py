from PIL import Image

FIXEXP = True  # Flag to fix underexposition
MINFACE = 8  # Minimum face size ratio; too low and we get false positives
INCREMENT = 0.06
GAMMA_THRES = 0.001
GAMMA = 0.90
FACE_RATIO = 6  # Face / padding ratio
QUESTION_OVERWRITE = "Overwrite image files?"
CASCFILE = "haarcascade_frontalface_default.xml"

PILLOW_FILETYPES = [k for k in Image.registered_extensions().keys()]
INPUT_FILETYPES = PILLOW_FILETYPES + [s.upper() for s in PILLOW_FILETYPES]
