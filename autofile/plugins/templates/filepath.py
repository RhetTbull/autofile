"""Plugin template for autofile to manipulate filepath """

import pathlib
import shlex
from typing import Iterable, List, Optional

import autofile
from autofile.path_utils import sanitize_dirname, sanitize_pathpart

FIELDS = {"{filepath}": "The full path to the file being processed"}

SUBFIELDS = {
    "name": "The name of the file",
    "stem": "The name of the file without the suffix (extension)",
    "suffix": "The suffix (extension) of the file, including the leading `.`",
    "parent": "The parent directory of the file",
}


@autofile.hookimpl
def get_template_help() -> Iterable:
    text = """
    The `{filepath}` fields returns the full path to the source file being processed. 
    Various attributes of the path can be accessed using "dot notation" (appended to the filepath field with a '.'). 
    For example, 
    `{filepath.name}` returns just the name of the file without the full path. 
    `{filepath.parent}` returns the parent directory of the file.
    
    Path attributes can be chained, for example `{filepath.parent.name}` returns just the name of the immediate parent directory without the full directory path.

    For example, if the field `{filepath}` is `'/Shared/files/IMG_1234.JPG'`:

    - `{filepath.parent}` is `'/Shared/files'`
    - `{filepath.name}` is `'IMG_1234.JPG'`
    - `{filepath.stem}` is `'IMG_1234'`
    - `{filepath.suffix}` is `'.JPG'`

    The following attributes are available:
    
    """
    fields = [["Field", "Description"], *[[k, v] for k, v in FIELDS.items()]]
    subfields = [["Subfield", "Description"], *[[k, v] for k, v in SUBFIELDS.items()]]
    return ["**File Path Fields**", fields, text, subfields]


@autofile.hookimpl
def get_template_value(
    filepath: str, field: str, subfield: str, default: List[str]
) -> Optional[List[Optional[str]]]:
    """lookup value for template pathlib template fields

    Args:
        field: template field to find value for.

    Returns:
        The matching template value (which may be None).
    """
    field_stem = field.split(".")[0]
    if field_stem != "filepath":
        return None

    return [_get_pathlib_value(field, filepath)]


def _get_pathlib_value(field, value, quote=False):
    """Get the value for a pathlib.Path type template

    Args:
        field: the path field, e.g. "filename.stem"
        value: the value for the path component
        quote: bool; if true, quotes the returned path for safe execution in the shell
    """
    parts = field.split(".")

    if len(parts) == 1:
        return shlex.quote(value) if quote else value

    path = pathlib.Path(value)
    for attribute in parts[1:]:
        try:
            val = getattr(path, attribute)
            path = pathlib.Path(val)
        except AttributeError:
            raise ValueError(f"Illegal value for path template: {attribute}")

    val_str = str(val)
    if quote:
        val_str = shlex.quote(val_str)
    return val_str
