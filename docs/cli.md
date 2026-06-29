---
layout: default
title: CLI
heading: Command line
lead: Use autocrop directly, or compose it with shell tools for larger jobs.
description: autocrop command-line usage and shell examples.
---

## Single-image usage

Autocrop v2 behaves like a classic shell command: one input image is cropped,
cropped image bytes go to stdout by default, and diagnostics go to stderr.

```sh
autocrop portrait.jpg > portrait-cropped.jpg
cat portrait.jpg | autocrop - > portrait-cropped.jpg
autocrop portrait.jpg -o portrait-cropped.jpg
autocrop portrait.jpg -o cropped/
```

YuNet is the built-in face detector; there is no detector-selection flag.

## Shell-composed batch jobs

Autocrop intentionally does not walk directories. For recursive or filtered
batch jobs, compose it with shell tools:

```sh
mkdir -p cropped
find portraits -type f \( -iname '*.jpg' -o -iname '*.png' \) -print0 |
  while IFS= read -r -d '' file; do
    out="cropped/${file#portraits/}"
    mkdir -p "$(dirname "$out")"
    autocrop "$file" > "$out"
  done
```

Convert output to JPEG while batching:

```sh
mkdir -p cropped
find portraits -type f \( -iname '*.jpg' -o -iname '*.png' \) -print0 |
  while IFS= read -r -d '' file; do
    out="cropped/${file#portraits/}"
    mkdir -p "$(dirname "$out")"
    autocrop "$file" -e jpg > "${out%.*}.jpg"
  done
```

With `fd`:

```sh
fd -e jpg -e png . portraits -x sh -c 'out="cropped/${1#portraits/}"; mkdir -p "$(dirname "$out")"; autocrop "$1" > "$out"' sh {}
```

With `xargs`:

```sh
find portraits -type f \( -iname '*.jpg' -o -iname '*.png' \) -print0 |
  xargs -0 -I{} sh -c 'out="cropped/${1#portraits/}"; mkdir -p "$(dirname "$out")"; autocrop "$1" > "$out"' sh {}
```
