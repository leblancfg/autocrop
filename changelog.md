# Autocrop changelog

## 0.2.0

### Changes
* Add -o, --output flag to specify directory where cropped images are to be dumped.
	- Error out if output folder set to current directory, i.e. -o .
	- If directory doesn't exist yet, create it.
	- If no face can be found in an image in batch, it is still copied over to -o folder.
	- If no output folder is added, ask for confirmation ([Y]/n), and destructively crop images in-place.
* Use -i, --input flags as synonyms for -p or --path: symmetrical in meaning to "output".
	- Is now standard nomenclature in documentation.
* --input or --path flag is now optional.
	- Standard behaviour without input folder is to non-recursively process all images in immediate folder, i.e. -p . as currently implemented.

### Breaks
* Removed all mentions of the hard-coded 'bkp' and 'crop' folders
* Calling autocrop without specifying an input path, i.e. `autocrop` does not look for the 'images' folder anymore.
