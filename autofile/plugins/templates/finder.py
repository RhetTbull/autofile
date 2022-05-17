"""plugin for autofile to access Finder metadata (e.g. tags, comments); MacOS only"""

import sys

if sys.platform == "darwin":
    from ._finder_macos import get_template_help, get_template_value
