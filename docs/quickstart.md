---
layout: default
title: Quickstart
heading: Quickstart
lead: Install autocrop, crop one folder, then move to scriptable examples.
description: Install and run autocrop from the command line or Python.
---

## Install

```sh
pip install autocrop
```

For local development:

```sh
git clone https://github.com/leblancfg/autocrop
cd autocrop
python -m venv env
. env/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

## Crop a folder

```sh
autocrop -i portraits -o cropped -w 500 -H 500
```

Images with a detected face are written to `cropped`. Images without a detected
face are copied to the reject destination when one is configured.

## Crop from Python

```python
from autocrop import Cropper
from PIL import Image

cropper = Cropper(width=500, height=500, face_percent=50)
cropped = cropper.crop("portrait.jpg")

if cropped is not None:
    Image.fromarray(cropped).save("portrait-cropped.jpg")
```

`Cropper.crop()` returns `None` when no face is detected.
