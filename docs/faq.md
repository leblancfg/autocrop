---
layout: default
title: FAQ
heading: Upgrading to autocrop 2.0.0
lead: Fixing scripts and Python calls after an unpinned upgrade.
description: autocrop v1 to v2 migration FAQ, error messages, and rollback instructions.
---

Autocrop **2.0.0 was released on 2026-10-18**. This page covers migration from
published v1 releases and from the draft v2 diagnostics API.

## Migration checklist

| v1 call or behavior | 2.0.0 replacement |
| --- | --- |
| `image = cropper.crop(source)` | `result = cropper.crop(source)`; use `result.image` |
| `if image is not None` | `if result.image is not None` |
| `Cropper(..., padding=..., fix_gamma=...)` | Remove those arguments; use `face_percent` and post-process brightness |
| `autocrop -i folder -r rejected` | Invoke autocrop once per image in a shell loop |
| `autocrop -e png` | `autocrop image.jpg -o cropped.png` |
| `autocrop -v` for the version | `autocrop -V` or `autocrop --version` |
| Default in-place writes and prompts | Stdout by default; choose `-o` explicitly and keep backups |
| Haar detection and automatic brightening | YuNet detection, optional alignment, application-controlled brightness |

After updating your code, install `autocrop==2.0.0` in a clean environment, run
your tests on representative images, and regenerate your dependency lockfile.
If you need time to migrate, [pin v1](#rollback).

## Why did an unchanged script stop working? {#upgrade}

Autocrop 2.0.0 changes the command-line interface and removes some Python arguments.
A fresh install, environment rebuild, or `pip install --upgrade autocrop` can
select v2 if your requirement is `autocrop`, `autocrop>=1.3`, or another constraint
that permits it. An already-installed copy does not upgrade itself.

The CLI now crops one image per invocation. In Python, `crop()` now returns a
`CropResult`, not an array. **Every v1 Python caller must now read `result.image`.**
That field holds the RGB/RGBA array, or `None` when no crop is produced. See the
[Python return-value migration](#python-results); crop pixels can also differ.

Check what the affected environment actually runs:

```sh
python -m pip show autocrop
python -c 'import autocrop; print(autocrop.__version__, autocrop.__file__)'
autocrop --version
```

If the versions disagree, the `autocrop` command is probably from a different
environment. Use the executable in your application's virtual environment.

## How do I restore v1 while I update my code? {#rollback}

In the affected environment:

```sh
python -m pip install 'autocrop<2'
```

Also change your requirement to `autocrop<2` and regenerate your lockfile. For an
exact rollback, the last published v1 release is `autocrop==1.3.0`. The old
changelog mentions 1.3.1, but that version was not published to PyPI.

Test the restored environment before redeploying. An autocrop pin alone does
not freeze NumPy, OpenCV, or Pillow; keep a dependency lockfile if you need the
same environment on every deployment. Once migrated, use an explicit version
constraint or lockfile for v2 too.

## What replaces `-i`, directory inputs, and reject folders? {#directory-mode}

These commands no longer work:

```sh
autocrop -i portraits -o cropped -r rejected --no-confirm
autocrop portraits/
```

Removed options include `-i`/`--input`, `-r`/`--reject`, and
`--no-confirm`/`--skip-prompt`. V2 reports the removed option or directory input
and links here, rather than interpreting the directory as an invalid image.

Pass one image as the positional argument:

```sh
autocrop portraits/alice.jpg -o cropped/alice.jpg
```

For a batch, use a shell loop. This Bash example handles spaces in filenames and
keeps the originals:

```bash
mkdir -p cropped
for file in portraits/*.jpg portraits/*.png; do
  [ -f "$file" ] || continue
  if ! autocrop "$file" -o "cropped/$(basename "$file")"; then
    printf 'Not cropped: %s\n' "$file" >&2
  fi
done
```

There is no automatic reject-folder copy or batch summary. Your loop decides
what to do after a failure. Exit status 1 includes no-face, read, processing, and
write failures; use `--json diagnostics.json` to distinguish them rather than
assuming every failure means no face. See the [CLI examples](../cli/) for
recursive batches.

## Why does running `autocrop` alone fail or wait for input? {#no-input}

V1 scanned the current directory. V2 requires an image filename, or reads image
bytes from stdin when it is piped or redirected. With a terminal on stdin and
no filename, it reports that an input image is required. An empty pipe produces
an empty-input error; an open pipe can wait for its writer to finish.

```sh
autocrop portrait.jpg -o cropped.jpg
cat portrait.jpg | autocrop - > cropped.jpg
```

The short version flag is now **`-V`**, not `-v`. Lowercase `-v` enables timings
and does not bypass cropping. Use `autocrop --version` in scripts.

## Why is my terminal full of binary data, or my output file missing? {#stdout}

Without `-o`, v2 writes the cropped image to stdout. It does not overwrite the
input by default. Capture stdout or choose an explicit output file:

```sh
autocrop portrait.jpg > cropped.jpg
autocrop portrait.jpg -o cropped.jpg
```

Messages and timings go to stderr. Do not merge stderr into an image stream with
`2>&1`. Python subprocess callers should capture image output as bytes, not use
`text=True`.

Stdin input currently writes only to stdout. `autocrop - -o cropped.jpg` is
rejected instead of silently ignoring `-o`; use redirection, preserving the
input's format, or save the source to a file first. For Windows PowerShell,
prefer filename input with `-o`: older PowerShell versions can corrupt native
binary output during redirection.

Never redirect onto the source itself (`autocrop portrait.jpg > portrait.jpg`):
the shell truncates that file before autocrop reads it. Explicit
`-o portrait.jpg` requests an in-place overwrite without a confirmation prompt;
keep a backup if you use it.

Shell redirection also creates or truncates the destination even when cropping
fails. Check the exit status, or use `-o` to avoid an empty file on a no-face result.

## What replaces `-e`/`--extension`? {#output-format}

Choose a supported extension on the explicit output filename:

```sh
# Old: autocrop -i portraits -e png
# New, for one image:
autocrop portrait.jpg -o cropped.png
```

Redirection does not choose an encoder: `autocrop portrait.jpg > cropped.png`
still produces JPEG bytes. Stdout keeps the input format when writable and uses
PNG as a fallback. Use `-o` when converting formats. An output directory keeps
the source filename and extension. Unsupported output extensions produce an
error before image processing.

## Why does `Cropper` reject my Python arguments? {#python-arguments}

`padding`, `fix_gamma`, and detector-selection arguments are no longer supported.
V2 raises `TypeError` with a migration explanation instead of ignoring them.
Only `width`, `height`, and `face_percent` may be positional. This prevents v1's
fourth and fifth arguments from silently acquiring new meanings.

```python
# Old:
# Cropper(500, 500, 50, None, False)
# Cropper(width=500, padding=None, fix_gamma=False)

# New:
from autocrop import Cropper
cropper = Cropper(width=500, height=500, face_percent=50, resize=True)
result = cropper.crop("portrait.jpg")
```

`padding` was ignored in v1. Remove it; use `face_percent` to control margins.
Automatic gamma/brightness adjustment is gone, so removing `fix_gamma=False`
keeps that intent. If you used `fix_gamma=True`, apply your chosen brightness
adjustment after cropping. Smaller `face_percent` values request more context
around the face, subject to the image bounds.

Use keyword arguments for `resize`, `align`, and other options.

## Why does my array code fail, or my no-face check no longer work? {#python-results}

`crop()` always returns a `CropResult`. Code such as `Image.fromarray(cropped)`,
`cropped.shape`, or `if cropped is not None` must access `.image` instead:

```python
result = cropper.crop("portrait.jpg")
if result.image is not None:
    from PIL import Image
    Image.fromarray(result.image).save("cropped.jpg")
else:
    print(result.diagnostics.error)
```

The result record exists even when its image is `None`. `if result` and
`bool(result)` raise `TypeError` explaining the required check. Indexing,
`len(result)`, and unpacking also raise migration errors; `.shape`, `.dtype`, and other
missing array attributes explain that you need `.image`.

Python identity comparisons cannot be intercepted: `result is not None` is
always true, and `result is None` is always false. Update those checks yourself.
Third-party libraries may produce their own errors (or treat the record as an
object); pass them the checked image array. For the smallest change to v1 code,
replace `cropped = cropper.crop(source)` with `cropped = cropper.crop(source).image`.

Diagnostics are a per-call `CropDiagnostics` dataclass. Read attributes such as
`result.diagnostics.crop_rectangle`, or use `dataclasses.asdict()` to serialize
it. There is no flag, tuple unpacking, or `cropper.diagnostics` state. Unreadable
files and configuration errors still raise. The earlier diagnostics flag and
separate method existed only in draft PRs, not published releases:

```python
# Draft API, no longer supported:
# image, diagnostics = cropper.crop(source, diagnostics=True)
# image, diagnostics = cropper.crop_with_diagnostics(source)
# diagnostics = cropper.diagnostics

# 2.0.0:
result = cropper.crop(source)
image = result.image
diagnostics = result.diagnostics
```

These draft calls now fail with a link to this section. Do not add a diagnostics
flag or cache last-call state in a shared cropper.

V1 code that treated unreadable files as `None` must now catch `OSError`
(including `FileNotFoundError` and Pillow's `UnidentifiedImageError`). A completed
no-face attempt still returns a result, with `result.image is None`; it is not
an I/O failure. Invalid configuration raises `TypeError` or `ValueError`.

## What replaces removed Python helpers and constants? {#python-helpers}

These were internal helpers, not a supported public API. Imports now fail with
an `ImportError` containing a migration link; removed `Cropper` attributes raise
an explanatory `AttributeError`. Assigning `cropper.gamma`, `cropper.casc_path`,
or `cropper.diagnostics` also raises instead of silently creating unused state.

| Removed name | Replacement |
| --- | --- |
| `autocrop.cli.main` | Loop over files and use `Cropper.crop(source).image` |
| `autocrop.cli.reject` | Copy failed inputs yourself, for example with `shutil.copy2` |
| `autocrop.cli.output_path` | Create directories with `pathlib.Path.mkdir` |
| `autocrop.cli.chk_extension` | Choose the output filename extension (`-o cropped.png`) |
| `autocrop.cli.confirmation`, `compat_input` | Implement prompts in your own application; use Python's `input()` |
| `autocrop.autocrop.gamma`, `check_underexposed` | Apply your chosen brightness correction to `result.image` |
| `cropper.gamma`, `cropper.casc_path` | Remove access; automatic brightening and the Haar model are gone |
| `CV2_FILETYPES`, `PILLOW_FILETYPES`, `COMBINED_FILETYPES` | Use `autocrop.constants.INPUT_FILETYPES` |
| `FIXEXP`, `GAMMA`, `GAMMA_THRES` | Configure brightness in your own code |
| `MINFACE`, `INCREMENT`, `CASCFILE` | Remove Haar-specific configuration; YuNet is built in |
| `FACE_RATIO` | Use `Cropper(face_percent=...)` for margins |
| `QUESTION_OVERWRITE` | Keep any overwrite prompt in your own application |

`ImageReadError` now inherits from `Exception` rather than `BaseException`.
Image files are decoded with Pillow; catch `OSError` for unreadable files instead
of relying only on the old custom exception.

The input format list describes Pillow's recognized extensions; some decoders
still require system support. It does not guarantee that every file can be read.
Unsupported input objects and numeric options still have validation gaps. See
the [known SDK limitations and workarounds](../api/#input-and-ownership-limitations).

## Why are the crops, colors, or brightness different? {#different-results}

V2 replaces the Haar cascade with a neural-network detector and selects the
largest detected face. Face boxes, accepted faces, and crop boundaries can
change. There is no flag to restore the old detector. Compare representative
images before updating pixel snapshots or deploying.

V2 also applies EXIF orientation before cropping, clamps crop bounds, uses
Pillow for resizing, preserves alpha, and no longer brightens dark crops
automatically. These changes can alter pixels even when your API call is unchanged.

NumPy inputs use OpenCV's BGR/BGRA channel order; outputs use RGB/RGBA for Pillow.
An RGB array from Pillow must be converted before passing it in. Passing a
filename avoids that conversion. Do not save the returned RGB array through
`cv2.imwrite` without converting it to BGR first.

Alignment is opt-in (`Cropper(align=True)` or `--align`). Without that option,
v2 does not level tilted faces. With it, rotation interpolates pixels even when
resizing is disabled. See the [API documentation](../api/) for diagnostics and
coordinate conventions.

## Why does installation fail, stay on v1, or complain about OpenCV? {#dependencies}

V2 requires Python 3.10 or newer, `opencv-python-headless>=4.8,<5`, and
`Pillow>=12.3.0`. The Pillow minimum includes fixes for reported image-decoding
and memory-safety vulnerabilities. An older Pillow pin conflicts with v2; update
it and test your application's image handling.

On older Python, an unpinned installer can select v1 instead; explicitly requesting v2
fails. Upgrade Python to use v2, or keep a compatible v1 environment.

An existing OpenCV pin below 4.8 conflicts with v2. Multiple OpenCV distributions
(`opencv-python`, `opencv-python-headless`, and the contrib variants) share the
`cv2` import and can leave an inconsistent installation. Inspect the affected
environment:

```sh
python -m pip check
python -m pip list
python -c 'import cv2; print(cv2.__version__, cv2.__file__)'
```

Test in a clean Python 3.10+ virtual environment before changing a shared one.
Let autocrop install its declared dependencies, then resolve any application
pins deliberately. Autocrop can explain missing detector support at runtime,
but cannot intercept pip resolver errors or a broken `cv2` import.

The default model ships inside the package; cropping does not download it.
A missing-model error usually means a damaged installation or a wrong custom
model path. Check that path or reinstall autocrop. A new detector can legitimately
return no face for an image v1 accepted; that is distinct from an installation error.
