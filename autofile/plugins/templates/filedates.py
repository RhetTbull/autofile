"""Plugin for autofile template to process file dates"""

import datetime
import os
import sys
from typing import Iterable, List, Optional

import autofile
from autofile.datetime_formatter import DateTimeFormatter
from autofile.datetime_utils import datetime_utc_to_local

TODAY = None

FIELDS = {
    "{created}": "File creation date/time (MacOS only; only other platforms returns file inode change time)",
    "{modified}": "File modification date/time",
    "{accessed}": "File last accessed date/time",
    "{today}": "The current date/time (as of when {today} is first evaluated)",
    "{now}": "The current date/time (evaluated at the time the template is processed)",
}

DATETIME_ATTRIBUTES = {
    "date": "ISO date, e.g. 2020-03-22",
    "year": "4-digit year, e.g. 2021",
    "yy": "2-digit year, e.g. 21",
    "month": "Month name as locale's full name, e.g. December",
    "mon": "Month as locale's abbreviated name, e.g. Dec",
    "mm": "2-digit month, e.g. 12",
    "dd": "2-digit day of the month, e.g. 22",
    "dow": "Day of the week as locale's full name, e.g. Tuesday",
    "doy": "Julian day of year starting from 001",
    "hour": "2-digit hour, e.g. 10",
    "min": "2-digit minute, e.g. 15",
    "sec": "2-digit second, e.g. 30",
    "strftime": "Apply strftime template to date/time. Should be used in form "
    + "{created.strftime,TEMPLATE} where TEMPLATE is a valid strftime template, e.g. "
    + "{created.strftime,%Y-%U} would result in year-week number of year: '2020-23'. "
    + "If used with no template will return null value. "
    + "See https://strftime.org/ for help on strftime templates.",
}


@autofile.hookimpl
def get_template_help() -> Iterable:
    text = """
    Date/time fields may be formatted using "dot notation" attributes which are appended to the field name following a `.` (period). 
    For example, `{created.month}` resolves to the month name of the file's creation date in the user's locale, e.g. `December`. 

    The `{today}` and `{now}` fields resolve to the current date/time with one key distinction between them: 
    `{today}` is the current date/time as of when `{today}` is first evaluated and will remain unchanged for every file processed; 
    `{now}` is the current date/time at the time each template is processed and will change with every file processed. 

    The following attributes are available:
    
    """
    fields = [["Field", "Description"], *[[k, v] for k, v in FIELDS.items()]]
    attributes = [
        ["Attribute", "Description"],
        *[[k, v] for k, v in DATETIME_ATTRIBUTES.items()],
    ]
    return ["**Date/Time Fields**", fields, text, attributes]


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
    global TODAY

    field = field.split(".", 1)
    if "{" + field[0] + "}" not in FIELDS:
        return None

    stat_info = os.stat(filepath)
    dt = None
    if field[0] == "created":
        if sys.platform == "darwin":
            # MacOS provides file creation date/time
            dt = datetime.datetime.fromtimestamp(stat_info.st_birthtime)
        else:
            # use ctime for other platforms which is last inode change
            dt = datetime.datetime.fromtimestamp(stat_info.st_ctime)
    elif field[0] == "modified":
        dt = datetime.datetime.fromtimestamp(stat_info.st_mtime)
    elif field[0] == "accessed":
        dt = datetime.datetime.fromtimestamp(stat_info.st_atime)
    elif field[0] == "today":
        if TODAY is None:
            # initialize TODAY only the first time the template is evaluated
            TODAY = datetime_utc_to_local(datetime.datetime.now(datetime.timezone.utc))
        dt = TODAY
    elif field[0] == "now":
        dt = datetime_utc_to_local(datetime.datetime.now(datetime.timezone.utc))
    else:
        raise ValueError(f"Unknown field {field}")

    if len(field) == 1:
        return [dt.isoformat()]

    subfield = field[1]
    if subfield not in DATETIME_ATTRIBUTES:
        raise ValueError(f"Unknown subfield {subfield}")

    if subfield == "strftime":
        if default:
            try:
                value = dt.strftime(default[0]) if dt else None
            except:
                raise ValueError(f"Invalid strftime template: '{default}'")
        else:
            value = None
        return [value]
    return [getattr(DateTimeFormatter(dt), subfield)]
