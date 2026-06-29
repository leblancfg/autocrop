---
layout: default
title: Migration path
heading: Migration path
lead: Proposed breaking changes and migration notes for the next major release.
description: autocrop migration notes and next major release direction.
---

## Goals

- make the CLI composable and pipeable
- keep file output explicit and predictable
- support better face detection through YuNet
- preserve image and filesystem metadata where possible
- modernize development workflow around just and uv

## CLI changes under discussion

The current CLI is folder-first. The next major release should make single-image
mode the default shape and move recursive workflows to shell composition.

```sh
autocrop portrait.jpg > cropped.jpg
find portraits -type f -name '*.jpg' -print0 | xargs -0 -I{} sh -c 'autocrop "$1" > "cropped/$(basename "$1")"' sh {}
```

## Detector changes under discussion

YuNet is likely useful for the next major release, but it changes detection
behavior. The proposed shape is:

- Haar remains available
- YuNet is added behind an explicit detector option first
- the docs explain model source, licensing, and threshold tradeoffs

## Packaging changes

The migration path should align runtime and contributor paths:

- Python 3.10-3.14 support
- `just` for project commands
- `uv` for environment, dependency, and CI execution
