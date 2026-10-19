# -*- coding: utf-8 -*-

import os
import sys

from . import timing
from .__version__ import __version__
from .autocrop import Cropper
from .cli import command_line_interface
from .diagnostics import CropDiagnostics, CropResult

__all__ = ["Cropper", "CropResult", "CropDiagnostics", "command_line_interface", "__version__"]

timing.mark_imports_complete()

__doc__ = """
Image cropping module for Python with face detection
====================================================
Autocrop is a Python module that provides a simple and efficient
method of cropping images of people around their faces.

See https://leblancfg.com/autocrop for more documentation.
"""

# Inject vendored directory into system path.
v_path = os.path.abspath(os.path.sep.join([os.path.dirname(os.path.realpath(__file__)), "vendor"]))
sys.path.insert(0, v_path)

# Inject patched directory into system path.
v_path = os.path.abspath(os.path.sep.join([os.path.dirname(os.path.realpath(__file__)), "patched"]))
sys.path.insert(0, v_path)

if __name__ == "__main__":
    command_line_interface()
