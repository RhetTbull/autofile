"""Template plugins for autofile to format strings and strip whitespace"""

from typing import Iterable, List, Optional

import autofile
from autofile.datetime_formatter import DateTimeFormatter

FIELDS = {
    "{strip}": "Use in form '{strip,TEMPLATE}'; strips whitespace from begining and end of rendered TEMPLATE value(s).",
    "{format}": "Use in form, '{format:TYPE:FORMAT,TEMPLATE}'; converts TEMPLATE value to TYPE then formats the value using python string formatting codes specified by FORMAT; TYPE is one of: 'int', 'float', or 'str'.",
}


@autofile.hookimpl
def get_template_help() -> Iterable:
    text = """
    The `{strip}` and `{format}` fields are used to format strings. 
    `{strip,TEMPLATE}` strips whitespace from TEMPLATE. 
    For example, `{strip,{exiftool:Title}}` will strip any excess whitespace from the title of an image file. 

    `{format:TYPE:FORMAT,TEMPLATE}` formats TEMPLATE using python string formatting codes. 
    For example: 
    
    - `{format:int:02d,{audio:track}}` will format the track number of an audio file to two digits with leading zeros. 
    - `{format:str:-^30,{audio.title}}` will center the title of an audio file and pad it to 30 characters with '-'.

    TYPE must be one of 'int', 'float', or 'str'. 
    See https://docs.python.org/3.7/library/string.html#formatspec for more information on valid FORMAT values.
    """
    fields = [["Field", "Description"], *[[k, v] for k, v in FIELDS.items()]]
    return ["**String Formatting Fields**", fields, text]


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
    if field == "strip":
        return [v.strip() for v in default]

    if field == "format":
        if not subfield or ":" not in subfield:
            raise ValueError("{format} requires subfield in form TYPE:FORMAT")
        type_, format_str = subfield.split(":", 1)
        if type_ not in ("int", "float", "str"):
            raise ValueError(
                f"'{type_}' is not a valid type for {format}: must be one of 'int', 'float', 'str'"
            )
        if type_ == "int":
            default = [int(v) for v in default]
        elif type_ == "float":
            default = [float(v) for v in default]
        return [format_str_value(v, format_str) for v in default]

    return None


def format_str_value(value, format_str):
    """Format value based on format code in field in format id:02d"""
    if not format_str:
        return str(value)
    format_str = "{0:" + f"{format_str}" + "}"
    return format_str.format(value)
