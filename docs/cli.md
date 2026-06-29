---
layout: default
title: CLI
heading: Command line
lead: Use autocrop directly, or compose it with shell tools for larger jobs.
description: autocrop command-line usage and shell examples.
---

## Single-image usage

Autocrop v2 behaves like a classic shell command for single images: cropped image
bytes go to stdout and diagnostics go to stderr.

```sh
autocrop portrait.jpg > portrait-cropped.jpg
cat portrait.jpg | autocrop - > portrait-cropped.jpg
autocrop portrait.jpg -o portrait-cropped.jpg
```

YuNet is the built-in face detector; there is no detector-selection flag.

## Directory usage

Directory input requires an explicit output directory:

```sh
autocrop -i portraits -o cropped
autocrop -i portraits -o cropped -w 400 -H 400
autocrop -i portraits -o cropped -e png
autocrop -i portraits -o cropped --no-resize
autocrop -i portraits -o cropped -r rejected
```

Explicit in-place directory output remains available by passing the same input
and output directory. It prompts unless `--no-confirm` is passed.

```sh
autocrop -i portraits -o portraits
```

## Shell-composed batch jobs

For recursive or filtered batch jobs, compose `autocrop` with shell tools:

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
