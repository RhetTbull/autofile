"""plugin for autofile to access Finder metadata (e.g. tags, comments)"""

from osxmetadata import OSXMetaData
from typing import Dict, Iterable, List, Optional

import autofile
from autofile.datetime_utils import datetime_naive_to_utc

FIELDS = {
    "{finder}": "Get metadata managed by macOS Finder such as tags and comments; use in form '{finder:SUBFIELD}', e.g. '{finder:tags}'",
}

SUBFIELDS = {"tags": "Finder tags (keywords)", "comment": "Finder comment"}


@autofile.hookimpl
def get_template_help() -> Iterable:
    text = """
    `{finder}` provides access to Finder metadata. It must be used in the form `{finder:SUBFIELD}`
    where SUBFIELD is one of the following:
    """

    fields = [["Field", "Description"], *[[k, v] for k, v in FIELDS.items()]]
    subfields = [["Subfield", "Description"], *[[k, v] for k, v in SUBFIELDS.items()]]
    return ["**Finder Metadata**", fields, text, subfields]


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
    if "{" + field + "}" not in FIELDS:
        return None
    if not subfield or subfield not in SUBFIELDS:
        raise ValueError(f"Missing or invalid subfield '{subfield}'")

    metadata = OSXMetaData(filepath)
    if subfield == "tags":
        tags = metadata.tags
        return [tag.name for tag in tags]
    elif subfield == "comment":
        comment = metadata.findercomment
        return [str(comment)]
