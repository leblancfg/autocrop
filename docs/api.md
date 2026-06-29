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

### Parameters

- `width`: output crop width in pixels.
- `height`: output crop height in pixels.
- `face_percent`: target face height as a percentage of output height.
- `padding`: legacy padding parameter.
- `fix_gamma`: brighten underexposed images before detection.
- `resize`: resize output to `width` and `height` when true.

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

## Migration notes

The next major release should make detector choice explicit, including YuNet
support, while keeping Haar available for compatibility during the transition.
