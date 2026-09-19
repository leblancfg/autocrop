import itertools
import os
from typing import Protocol, cast

import cv2
import numpy as np
from PIL import Image, ImageOps

from .types import ImageArray
from .yunet import YuNetDetector


class ImageReadError(Exception):
    """Raised when an input cannot be interpreted as an image array."""

    pass


class FaceDetector(Protocol):
    """Existing custom-detector interface: an array of bounding-box rows."""

    def detect(self, image: ImageArray) -> ImageArray: ...


def perp(a: ImageArray) -> ImageArray:
    b = np.empty_like(a)
    b[0] = -a[1]
    b[1] = a[0]
    return b


def intersect(v1: ImageArray, v2: tuple[ImageArray, ImageArray]) -> ImageArray | None:
    a1, a2 = v1
    b1, b2 = v2
    da = a2 - a1
    db = b2 - b1
    dp = a1 - b1
    dap = perp(da)
    denom = np.dot(dap, db).astype(float)
    if denom == 0:
        return None
    num = np.dot(dap, dp)
    return np.asarray((num / denom) * db + b1)


def distance(pt1: ImageArray, pt2: tuple[int, int] | ImageArray) -> float:
    """Returns the euclidian distance in 2D between 2 pts."""
    return float(np.linalg.norm(pt2 - pt1))


def bgr_to_rbg(img: ImageArray) -> ImageArray:
    """Given a BGR (cv2) numpy array, returns a RBG (standard) array."""
    # Don't do anything for grayscale images
    if img.ndim == 2:
        return img

    # Flip the channels. Use explicit indexing in case RGBA is used.
    img[:, :, [0, 1, 2]] = img[:, :, [2, 1, 0]]
    return img


def detector_color_image(image: ImageArray, image_is_bgr: bool) -> ImageArray:
    """
    Return a 3-channel BGR image suitable for OpenCV DNN face detectors.

    The crop itself still uses the original image array, so grayscale and alpha
    channels can be preserved in the returned crop.
    """
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    channels = image.shape[2]
    if channels == 1:
        return cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2BGR)
    if channels == 4:
        if image_is_bgr:
            return image[:, :, :3].copy()
        return cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
    if channels == 3:
        if image_is_bgr:
            return image
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    return image


def check_positive_scalar(num: int | float) -> int:
    """Returns True if value if a positive scalar."""
    is_scalar = np.isscalar(num)
    if num > 0 and not isinstance(num, str) and is_scalar:
        # NumPy's scalar TypeGuard is broader than this function's numeric input contract.
        return int(cast(int | float, num))
    raise ValueError("A positive scalar is required")


def open_file(input_filename: str | os.PathLike[str]) -> ImageArray:
    """Given a filename, returns an EXIF-oriented numpy array."""
    with Image.open(input_filename) as img_orig:
        return np.array(ImageOps.exif_transpose(img_orig))


class Cropper:
    """
    Crops the largest detected face from images.

    This class uses OpenCV's YuNet face detector to perform the
    `crop` by taking in either a filepath or Numpy array, and
    returning a Numpy array.

    Parameters:
    -----------

    * `width` : `int`, default=500
        - The width of the resulting array.
    * `height` : `int`, default=`500`
        - The height of the resulting array.
    * `face_percent`: `int`, default=`50`
        - Aka zoom factor. Percent of the overall size of
        the cropped image containing the detected coordinates.
    * `resize`: `bool`, default=`True`
        - Resizes the image to the specified width and height,
        otherwise, returns the original image pixels.

    NumPy array inputs are interpreted as OpenCV-style BGR/BGRA arrays. Returned
    arrays are RGB/RGBA so they can be passed directly to Pillow or Matplotlib.
    """

    def __init__(
        self,
        width: int = 500,
        height: int = 500,
        face_percent: int = 50,
        resize: bool = True,
        face_detector: FaceDetector | None = None,
        yunet_model_path: str | os.PathLike[str] | None = None,
        yunet_score_threshold: float = 0.6,
        yunet_nms_threshold: float = 0.3,
        yunet_top_k: int = 5000,
    ) -> None:
        self.height = check_positive_scalar(height)
        self.width = check_positive_scalar(width)
        self.aspect_ratio = width / height
        self.resize = resize
        self.face_detector: FaceDetector = face_detector or YuNetDetector(
            model_path=yunet_model_path,
            score_threshold=yunet_score_threshold,
            nms_threshold=yunet_nms_threshold,
            top_k=yunet_top_k,
        )

        # Face percent
        if face_percent > 100 or face_percent < 1:
            fp_error = "The face_percent argument must be between 1 and 100"
            raise ValueError(fp_error)
        self.face_percent = check_positive_scalar(face_percent)

    def crop(self, path_or_array: str | ImageArray) -> ImageArray | None:
        """
        Given a file path or np.ndarray image with a face,
        returns cropped np.ndarray around the largest detected
        face.

        Parameters
        ----------
        - `path_or_array` : {`str`, `np.ndarray`}
            * The filepath or numpy array of the image. Array inputs are
              interpreted as OpenCV-style BGR/BGRA arrays.

        Returns
        -------
        - `image` : {`np.ndarray`, `None`}
            * A cropped numpy array if face detected, else None.
        """
        if isinstance(path_or_array, str):
            image = open_file(path_or_array)
            image_is_bgr = False
        else:
            image = path_or_array
            image_is_bgr = True

        detection_image = detector_color_image(image, image_is_bgr)

        # Scale the image
        try:
            img_height, img_width = image.shape[:2]
        except AttributeError:
            raise ImageReadError
        # ====== Detect faces in the image ======
        faces = self.face_detector.detect(detection_image)

        # Handle no faces
        if len(faces) == 0:
            return None

        # Make crop margins from biggest face found
        x, y, w, h = max(faces, key=lambda face: face[2] * face[3])
        if w <= 0 or h <= 0:
            return None
        pos = self._crop_positions(
            img_height,
            img_width,
            x,
            y,
            w,
            h,
        )

        if pos[0] >= pos[1] or pos[2] >= pos[3]:
            return None

        # ====== Actual cropping ======
        image = image[pos[0] : pos[1], pos[2] : pos[3]]

        # Resize
        if self.resize:
            with Image.fromarray(image) as img:
                image = np.array(img.resize((self.width, self.height)))

        if image_is_bgr:
            return bgr_to_rbg(image)
        return image

    def _determine_safe_zoom(self, imgh: int, imgw: int, x: int, y: int, w: int, h: int) -> float:
        """
        Determines the safest zoom level with which to add margins
        around the detected face. Tries to honor `self.face_percent`
        when possible.

        Parameters:
        -----------
        imgh: int
            Height (px) of the image to be cropped
        imgw: int
            Width (px) of the image to be cropped
        x: int
            Leftmost coordinates of the detected face
        y: int
            Bottom-most coordinates of the detected face
        w: int
            Width of the detected face
        h: int
            Height of the detected face

        Diagram:
        --------
        i / j := zoom / 100

                  +
        h1        |         h2
        +---------|---------+
        |      MAR|GIN      |
        |         (x+w, y+h)|
        |   +-----|-----+   |
        |   |   FA|CE   |   |
        |   |     |     |   |
        |   ├──i──┤     |   |
        |   |  cen|ter  |   |
        |   |     |     |   |
        |   +-----|-----+   |
        |   (x, y)|         |
        |         |         |
        +---------|---------+
        ├────j────┤
                  +
        """
        # Find out what zoom factor to use given self.aspect_ratio
        corners = itertools.product((x, x + w), (y, y + h))
        center = np.array([x + int(w / 2), y + int(h / 2)])
        i = np.array([(0, 0), (0, imgh), (imgw, imgh), (imgw, 0), (0, 0)])  # image_corners
        image_sides = [(i[n], i[n + 1]) for n in range(4)]

        corner_ratios = [float(self.face_percent)]  # Hopefully we use this one
        for c in corners:
            corner_vector = np.array([center, c])
            a = distance(*corner_vector)
            intersects = list(intersect(corner_vector, side) for side in image_sides)
            for pt in intersects:
                if pt is None or not np.isfinite(pt).all():
                    continue
                if (pt >= 0).all() and (pt <= i[2]).all():  # if intersect within image
                    dist_to_pt = distance(center, pt)
                    if dist_to_pt > 0:
                        corner_ratios.append(100 * a / dist_to_pt)
        return max(corner_ratios)

    def _crop_positions(
        self,
        imgh: int,
        imgw: int,
        x: int,
        y: int,
        w: int,
        h: int,
    ) -> list[int]:
        """
        Retuns the coordinates of the crop position centered
        around the detected face with extra margins. Tries to
        honor `self.face_percent` if possible, else uses the
        largest margins that comply with required aspect ratio
        given by `self.height` and `self.width`.

        Parameters:
        -----------
        imgh: int
            Height (px) of the image to be cropped
        imgw: int
            Width (px) of the image to be cropped
        x: int
            Leftmost coordinates of the detected face
        y: int
            Bottom-most coordinates of the detected face
        w: int
            Width of the detected face
        h: int
            Height of the detected face
        """
        zoom = self._determine_safe_zoom(imgh, imgw, x, y, w, h)

        # Adjust output height based on percent
        if self.height >= self.width:
            height_crop = h * 100.0 / zoom
            width_crop = self.aspect_ratio * float(height_crop)
        else:
            width_crop = w * 100.0 / zoom
            height_crop = float(width_crop) / self.aspect_ratio

        # Calculate margins by centering face
        xpad = (width_crop - w) / 2
        ypad = (height_crop - h) / 2

        # Calc. positions of crop
        h1 = x - xpad
        h2 = x + w + xpad
        v1 = y - ypad
        v2 = y + h + ypad

        v1, v2, h1, h2 = int(v1), int(v2), int(h1), int(h2)

        if h1 < 0:
            h2 -= h1
            h1 = 0
        if h2 > imgw:
            h1 -= h2 - imgw
            h2 = imgw
        if v1 < 0:
            v2 -= v1
            v1 = 0
        if v2 > imgh:
            v1 -= v2 - imgh
            v2 = imgh

        return [
            max(0, v1),
            min(imgh, v2),
            max(0, h1),
            min(imgw, h2),
        ]
