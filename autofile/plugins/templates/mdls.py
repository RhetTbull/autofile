""" plugin for autofile to return mdls data; MacOS only"""

import sys

if sys.platform == "darwin":
    from ._mdls_macos import get_template_help, get_template_value
