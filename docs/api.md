---
layout: default
title: API
heading: Python API
lead: The core API is a small `Cropper` object that returns cropped image arrays.
description: autocrop Python API documentation.
---

## `Cropper`

```python
from autocrop import Cropper

cropper = Cropper(
    width=500,
    height=500,
    face_percent=50,
    resize=True,
)
```

Autocrop v2 uses OpenCV's YuNet neural-network face detector.

### Parameters

- `width`: output crop width in pixels.
- `height`: output crop height in pixels.
- `face_percent`: target face height as a percentage of output height.
- `padding`: legacy padding parameter; accepted for compatibility but ignored.
- `resize`: resize output to `width` and `height` when true.
- `yunet_model_path`: optional path to a compatible YuNet ONNX model.
- `yunet_score_threshold`: minimum detection confidence.
- `yunet_nms_threshold`: non-maximum suppression threshold.
- `yunet_top_k`: maximum detections to keep before NMS.

## `crop(path_or_array)`

```python
cropped = cropper.crop("portrait.jpg")
```

`path_or_array` may be a path or a NumPy array. The method returns a NumPy array
containing the cropped image, or `None` when no face is found.

```python
from PIL import Image

if cropped is not None:
    Image.fromarray(cropped).save("portrait-cropped.jpg")
```

Detection input is normalized internally to 3-channel BGR for YuNet. Cropping is
performed on the original image array, so grayscale and alpha channels are
preserved where Pillow/OpenCV can represent them.
