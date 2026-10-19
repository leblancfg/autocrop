---
layout: default
title: API
heading: Python API
lead: CropResult keeps an image and its diagnostics together.
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
- `resize`: resize output to `width` and `height` when true.
- `yunet_model_path`: optional path to a compatible YuNet ONNX model.
- `yunet_score_threshold`: minimum detection confidence.
- `yunet_nms_threshold`: non-maximum suppression threshold.
- `yunet_top_k`: maximum detections to keep before NMS.

## `crop(path_or_array) -> CropResult`

```python
from PIL import Image

result = cropper.crop("portrait.jpg")

if result.image is not None:
    Image.fromarray(result.image).save("portrait-cropped.jpg")

print(result.diagnostics.crop_rectangle)
```

Every completed call returns a `CropResult` dataclass:

- `image`: an RGB/RGBA NumPy array, or `None` if no crop could be produced.
- `diagnostics`: a `CropDiagnostics` dataclass belonging to this attempt.

There is no diagnostics flag, tuple unpacking, or last-result attribute on
`Cropper`. **Check `result.image is not None`**, not `if result` or
`result is not None`: the result record exists even when cropping finds no face.
V1 code that expected an array must now read `.image`.

String filepaths are decoded with Pillow, applying EXIF orientation first.
NumPy inputs use OpenCV's BGR/BGRA channel order. Detection uses a normalized
3-channel image; the crop preserves grayscale and alpha where supported.
Unreadable files and invalid configuration still raise exceptions. No-face
results have `image=None` and `diagnostics.error="no_face_detected"`.

## `CropDiagnostics`

Import `CropResult` and `CropDiagnostics` from `autocrop`. Supporting records
live in `autocrop.diagnostics`: `ImageSize`, `Rectangle`, `DetectedFace`, `Point`,
and `DetectorDiagnostics`.

Diagnostics include detector settings, input/output dimensions, face boxes and
scores, selected face index, crop rectangle, resize mode, and the reason when
no crop was produced. Fields use attributes, not dictionary keys:

```python
face_index = result.diagnostics.selected_face_index
if face_index is not None:
    face = result.diagnostics.faces[face_index]
    print(face.box.width, face.score)
```

Boxes use `x`, `y`, `width`, and `height` in the EXIF-oriented input's pixel
coordinates, before resizing. Confidence scores are available for the built-in
detector; custom box-only detectors report `score=None`. Landmarks are decoded
by the detector adapter, so callers need not interpret detector-specific rows.

Use standard dataclass serialization for JSON. Do not serialize the whole
`CropResult`, which also contains the NumPy image:

```python
from dataclasses import asdict
import json

print(json.dumps(asdict(result.diagnostics)))
```

The package ships inline type hints and a `py.typed` marker. Type checkers can
narrow `result.image` after a None check and check diagnostic field access.
Array shape/dtype still depend on input mode; the annotations do not impose a
new runtime dtype restriction.

Each result owns its diagnostic records. Reusing a cropper does not overwrite
previous results, including after a failed call. The cropper's detector still
has internal caches; use separate cropper instances for concurrent processing.
