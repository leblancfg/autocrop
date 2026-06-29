from PIL import Image

GAMMA_THRES = 0.001
GAMMA = 0.90
QUESTION_OVERWRITE = "Overwrite image files?"
YUNET_MODEL = "face_detection_yunet_2023mar.onnx"

PILLOW_FILETYPES = [k for k in Image.registered_extensions().keys()]
INPUT_FILETYPES = PILLOW_FILETYPES + [s.upper() for s in PILLOW_FILETYPES]
