---
layout: default
title: CLI
heading: Command line
lead: Use autocrop directly, or compose it with shell tools for larger jobs.
description: autocrop command-line usage and shell examples.
---

## Current stable usage

```sh
autocrop -i portraits -o cropped
autocrop -i portraits -o cropped -w 400 -H 400
autocrop -i portraits -o cropped -e png
autocrop -i portraits -o cropped --no-resize
```

The stable CLI is folder-oriented and prompts before destructive in-place
cropping unless `--no-confirm` is passed.

## Next CLI direction

The next major CLI should behave more like a classic shell command:

- a single input image can be cropped to stdout
- diagnostics should go to stderr
- explicit output paths should still work
- recursive folder handling should be documented through shell tools, not owned by autocrop

```sh
autocrop portrait.jpg > portrait-cropped.jpg
cat portrait.jpg | autocrop - > portrait-cropped.jpg
```

For batch jobs:

```sh
mkdir -p cropped
find portraits -type f \( -iname '*.jpg' -o -iname '*.png' \) -print0 |
  while IFS= read -r -d '' file; do
    out="cropped/${file#portraits/}"
    mkdir -p "$(dirname "$out")"
    autocrop "$file" > "$out"
  done
```

With `fd`:

```sh
fd -e jpg -e png . portraits -x sh -c 'out="cropped/${1#portraits/}"; mkdir -p "$(dirname "$out")"; autocrop "$1" > "$out"' sh {}
```
