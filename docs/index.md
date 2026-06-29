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

Autocrop v2 uses OpenCV's YuNet neural-network detector and writes single-image
crops to stdout by default.

```sh
pip install autocrop
autocrop portrait.jpg > cropped.jpg
autocrop -i portraits -o cropped -w 500 -H 500
```

```python
from autocrop import Cropper
from PIL import Image

cropper = Cropper(width=500, height=500)
cropped = cropper.crop("portrait.jpg")

if cropped is not None:
    Image.fromarray(cropped).save("cropped.jpg")
```

## Documentation map

- [Quickstart]({{ '/quickstart/' | relative_url }}) covers installation and the shortest working examples.
- [CLI]({{ '/cli/' | relative_url }}) covers file, directory, and shell-composed workflows.
- [API]({{ '/api/' | relative_url }}) covers `Cropper` and return values.
- [Migration path]({{ '/migration/' | relative_url }}) tracks breaking changes.
