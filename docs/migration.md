---
layout: default
title: Migration path
heading: Migration path
lead: Breaking changes and migration notes for the next major release.
description: autocrop migration notes and next major release direction.
---

## Goals

- make the CLI composable and pipeable
- keep file output explicit and predictable
- replace Haar cascade detection with YuNet
- preserve image and filesystem metadata where possible
- modernize development workflow around just and uv

## CLI changes

Single-image mode writes cropped image bytes to stdout by default:

```sh
autocrop portrait.jpg > cropped.jpg
cat portrait.jpg | autocrop - > cropped.jpg
```

Directory mode requires an explicit output directory:

```sh
autocrop -i portraits -o cropped
```

Recursive workflows should use shell composition:

```sh
find portraits -type f -name '*.jpg' -print0 |
  xargs -0 -I{} sh -c 'autocrop "$1" > "cropped/$(basename "$1")"' sh {}
```

## Detector changes

Autocrop v2 uses YuNet only.

Removed:

- Haar cascade backend
- `--detector` CLI option
- bundled Haar cascade XML file

Added:

- vendored OpenCV Zoo YuNet ONNX model
- internal preprocessing for grayscale and RGBA inputs
- optional YuNet threshold constructor arguments for advanced Python API users

## Image adjustment changes

Automatic gamma/exposure adjustment was removed. If output brightening or color
correction is needed, compose autocrop with dedicated image-processing tools or
post-process the returned NumPy array in Python.

## Packaging changes

The migration path aligns runtime and contributor setup:

- Python 3.10-3.14 support
- `just` for project commands
- `uv` for environment, dependency, lockfile, and CI execution
- project and tool configuration centralized in `pyproject.toml`
