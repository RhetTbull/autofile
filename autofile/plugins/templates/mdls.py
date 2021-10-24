""" plugin for autofile to return mdls data"""

import datetime
import plistlib
import subprocess
from typing import Dict, Iterable, List, Optional

import autofile
from autofile.datetime_utils import datetime_naive_to_utc

FIELDS = {
    "{mdls}": "Get metadata attributes for file as returned by mdls command; use in form '{mdls:ATTRIBUTE}', for example, '{mdls:kMDItemContentType}'",
}

CACHED_MDLS_DATA = {}


@autofile.hookimpl
def get_template_help() -> Iterable:
    text = """
    `{mdls:ATTRIBUTE}` returns the value of the metadata ATTRIBUTE as returned by the macOS `mdls` command. 
    For example, `{mdls:kMDItemContentType}` returns the content type of the file, e.g. `public.python-script` or `public.mp3` 
    and `{mdls:kMDItemKind}` returns a description of file type, e.g. `Python Script` or `MP3 Audio`.
    """
    fields = [["Field", "Description"], *[[k, v] for k, v in FIELDS.items()]]
    return ["**macOS Metadata Fields**", fields, text]


@autofile.hookimpl
def get_template_value(
    filepath: str, field: str, subfield: str, default: List[str]
) -> Optional[List[Optional[str]]]:
    """lookup value for file dates

    Args:
        field: template field to find value for.

    Returns:
        The matching template value (which may be None).
    """
    if field != "mdls":
        return None

    if not subfield:
        raise ValueError(
            "{mdls} requires a subfield in form mdls:subfield, e.g. {mdls:kMDItemKind}"
        )

    global CACHED_MDLS_DATA
    if filepath in CACHED_MDLS_DATA:
        mdls = CACHED_MDLS_DATA[filepath]
        value = mdls.get(subfield)
        return value if type(value) == list else [value]

    mdls = load_mdls_data(filepath)
    CACHED_MDLS_DATA[filepath] = mdls
    value = mdls.get(subfield)
    return value if type(value) == list else [value]


def load_mdls_data(filepath: str) -> Dict:
    """load mdls data for file

    Args:
        filepath: path to file to load mdls data for

    Returns:
        dict of mdls data
    """
    cmd = ["mdls", "-plist", "-", filepath]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)
    mdls = plistlib.loads(proc.stdout)

    # plist returns naive datetime, should be UTC, not local timezone so convert if necessary
    for key, value in mdls.items():
        if isinstance(key, datetime.datetime):
            mdls[key] = datetime_naive_to_utc(value)
        else:
            mdls[key] = str(value)

    return mdls
