---
layout: default
title: autocrop
heading: autocrop
lead: Crop images around detected faces from Python or the shell.
description: Face-aware image cropping for scripts, data cleanup, and command-line workflows.
---

`autocrop` is a small Python package and CLI for cropping images around faces. It
is useful when you have portraits, screenshots, or scraped images and want
consistent framing without hand-editing each file.

## Version 2.0.0

Released 2026-10-18. This is a breaking release: Python calls return a
`CropResult`, and the CLI processes one image at a time. Read the
[migration FAQ]({{ '/faq/' | relative_url }}) to update v1 scripts, or check the
[changelog]({{ '/changelog/' | relative_url }}) for the full release notes.

Autocrop 2.0.0 uses OpenCV's YuNet neural-network detector and writes single-image
crops to stdout by default.

```sh
pip install autocrop
autocrop portrait.jpg > cropped.jpg
mkdir -p cropped
find portraits -type f -name '*.jpg' -print0 |
  xargs -0 -I{} sh -c 'autocrop "$1" > "cropped/$(basename "$1")"' sh {}
```

```python
from autocrop import Cropper
from PIL import Image

cropper = Cropper(width=500, height=500)
result = cropper.crop("portrait.jpg")

if result.image is not None:
    Image.fromarray(result.image).save("cropped.jpg")
```

## Documentation map

- [Quickstart]({{ '/quickstart/' | relative_url }}) covers installation and the shortest working examples.
- [CLI]({{ '/cli/' | relative_url }}) covers file and shell-composed workflows.
- [API]({{ '/api/' | relative_url }}) covers `Cropper` and return values.
- [Migration FAQ]({{ '/faq/' | relative_url }}) maps v1 calls and flags to v2, with rollback instructions.
- [Changelog]({{ '/changelog/' | relative_url }}) tracks release notes and v2 migration notes.
