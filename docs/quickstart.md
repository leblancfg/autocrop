---
layout: default
title: Quickstart
heading: Quickstart
lead: Install autocrop, crop one image, then move to scriptable examples.
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
uv sync
uv run autocrop --help
```

## Crop one image

```sh
autocrop portrait.jpg > portrait-cropped.jpg
```

Write to an explicit file or directory, or include timings on stderr:

```sh
autocrop portrait.jpg -o portrait-cropped.jpg
autocrop portrait.jpg -o cropped/
autocrop portrait.jpg --verbose > portrait-cropped.jpg
```

## Crop many images

Autocrop processes one image at a time. Use `find`, `fd`, or another file
selection tool for batch jobs:

```sh
mkdir -p cropped
find portraits -type f \( -iname '*.jpg' -o -iname '*.png' \) -print0 |
  while IFS= read -r -d '' file; do
    out="cropped/${file#portraits/}"
    mkdir -p "$(dirname "$out")"
    autocrop "$file" > "$out"
  done
```

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
