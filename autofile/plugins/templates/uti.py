"""Plugin for autofile template to process uti template; MacOS only

    On macOS <= 11 (Big Sur), uses objective C CoreServices methods
    UTTypeCopyPreferredTagWithClass and UTTypeCreatePreferredIdentifierForTag to retrieve the
    UTI and the extension.  These are deprecated in 10.15 (Catalina) and no longer supported on Monterey.

    On Monterey, these calls are replaced with Swift methods that I can't call from python so
    this code uses a cached dict of UTI values.  The code first checks to see if the extension or UTI
    is available in the cache and if so, returns it. If not, it performs a subprocess call to `mdls` to
    retrieve the UTI (by creating a temp file with the correct extension) and returns the UTI.  This only
    works for the extension -> UTI lookup. On Monterey, if there is no cached value for UTI -> extension lookup,
    returns None.

    It's a bit hacky but best I can think of to make this robust on different versions of macOS.  PRs welcome.
"""

import sys

if sys.platform == "darwin":
    from ._uti_macos import get_template_help, get_template_value
