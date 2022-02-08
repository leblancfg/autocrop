# Autocrop changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.3.1 - 2022-02-08
### API Additions
* The `Cropper` class now accepts a `resize` arg, to determine whether to resize the image after cropping it or not.
* Similarly for the CLI, it can now be called with a `--no-resize` flag

### Other changes
* The order of CLI args when calling `autocrop --help` changed to place flags first
* Start using type hints across the codebase

## 1.3.0 - 2022-01-25
### Changes

- The `initial-setup` step in Makefile now also installs development packages.
- The `black` formatting package now gets installed with `requirements-dev.txt`

### Deprecations

- Deprecate Python 3.6

## 1.2.0 - 2021-11-26
### Changes

- Modify the `opencv-python` dependency over to `opencv-python-headless`, which doesn't have all the GUI baggage. Easier to download and package.

### Documentation

- Created the `examples` directory and moved the example notebook to it.

## 1.1.1 - 17-02-2021
### Deprecations

- Deprecate Python 3.5
- Deprecate OpenCV 3

### API Additions

- User can now specify what file extension to save cropped files at the CLI

### Security

- Update Pillow dependency in order to limit possible security issues

### Other changes

- Updates to the developer setup tools and documentation
- Updates to the example notebook

## 1.1.0 - 24-10-2020
### Added

- CLI now copies file by default


## 1.0.0 - 24-03-2020
### Added

- Cropper class now available from Python API.
- Local multi-version testing for Python now available with `tox`.
- Extra regressions tests to defend against image warp and cropping outside the regions of interest.
- Support for Python 3.8

### Bugfixes

- Specify encoding in `setup.py`, which was causing some errors on Windows.

### Deprecated

- Support for padding argument &mdash; this is now solely handled by the `face_percent` parameter, and enforces the aspect ratio between `width` and `height`.
- Support for Python 2.7

## 0.3.2
### Changes

* Autocrop now prints the filename of images where face detection failed
* Internal refactoring and more tests

## 0.3.1
### Changes

* Add `-r`, `--reject` flag to specify directory where the images that autocrop *couldn't* find a face in are directed to.
* Instead of having the target files copied then cropped, they are instead cropped and saved to their respective target folder.

## 0.3.0
### Changes

* Added support for padding (`padLeft`, etc.) in the CLI.

### Bugfix

* Fixed warp on crop for `-w` and `-h` values

## 0.2.0
### Changes

* Add `-o`, `--output` flag to specify directory where cropped images are to be dumped.
	- Error out if output folder set to current directory, i.e. `-o .`
	- If directory doesn't exist yet, create it.
	- If no face can be found in an image in batch, it is still copied over to `-o` folder.
	- If no output folder is added, ask for confirmation ([Y]/n), and destructively crop images in-place.
* Use `-i`, `--input` flags as synonyms for `-p` or `--path`: symmetrical in meaning to "output".
	- Is now standard nomenclature in documentation.
* `--input` or `--path` flag is now optional.
	- Standard behaviour without input folder is to non-recursively process all images in immediate folder, i.e. `-p .` as currently implemented.

### Breaks

* Removed all mentions of the hard-coded 'bkp' and 'crop' folders
* Calling autocrop without specifying an input path, i.e. `autocrop` does not look for the 'images' folder anymore.
