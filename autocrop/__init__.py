# -*- coding: utf-8 -*-
# flake8: noqa

import os
import sys

from .autocrop import Cropper
from .cli import command_line_interface
from .__version__ import __version__

__doc__ = """
Image cropping module for Python with face detection
====================================================
Autocrop is a Python module that provides a simple and efficient
method of cropping images of people around their faces.

See https://leblancfg.com/autocrop for more documentation.
"""

# Inject vendored directory into system path.
v_path = os.path.abspath(
    os.path.sep.join([os.path.dirname(os.path.realpath(__file__)), "vendor"])
)
sys.path.insert(0, v_path)

# Inject patched directory into system path.
v_path = os.path.abspath(
    os.path.sep.join([os.path.dirname(os.path.realpath(__file__)), "patched"])
)
sys.path.insert(0, v_path)

if __name__ == "__main__":
    command_line_interface()
