"""Plugin template for autofile to manipulate filepath """

import pathlib
import shlex
from typing import Iterable, List, Optional

from autofile import hookimpl
from autofile.path_utils import sanitize_dirname, sanitize_pathpart
from autofile.renderoptions import RenderOptions

FIELDS = {"{filepath}": "The full path to the file being processed"}


@hookimpl
def get_template_help() -> Iterable:
    pass
    # return [FIELDS]


@hookimpl
def get_template_value(
    filepath: str, field: str, subfield: str, default: str, options: RenderOptions
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

    value = _get_pathlib_value(field, filepath, options.quote)

    if options.filename:
        value = sanitize_pathpart(value)
    elif options.dirname:
        value = sanitize_dirname(value)

    return [value]


def _get_pathlib_value(field, value, quote):
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
