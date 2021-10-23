"""Template plugins for autofile to strip whitespace"""

from typing import Iterable, List, Optional

from autofile import hookimpl
from autofile.datetime_formatter import DateTimeFormatter
from autofile.renderoptions import RenderOptions

FIELDS = {
    "{strip}": "Use in form '{strip,TEMPLATE}'; strips whitespace from begining and end of rendered TEMPLATE value(s).",
}


@hookimpl
def get_template_help() -> Iterable:
    pass
    # return [FIELDS]


@hookimpl
def get_template_value(
    filepath: str, field: str, subfield: str, default: str, options: RenderOptions
) -> Optional[List[Optional[str]]]:
    """lookup value for file dates

    Args:
        field: template field to find value for.

    Returns:
        The matching template value (which may be None).
    """
    if field == "strip":
        return [v.strip() for v in default]
    return None
