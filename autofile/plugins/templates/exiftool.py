"""exiftool template plugin for autofile"""

import datetime
from typing import Iterable, List, Optional

import autofile
from autofile.datetime_formatter import DateTimeFormatter
from autofile.exiftool import ExifToolCaching

FIELDS = {
    "{exiftool}": "Format: '{exiftool:GROUP:TAGNAME}'; use exiftool (https://exiftool.org) to extract metadata, "
    "in form GROUP:TAGNAME or TAGNAME, from image. "
    "E.g. '{exiftool:Make}' to get camera make, or {exiftool:IPTC:Keywords} to extract keywords. "
    "See https://exiftool.org/TagNames/ for list of valid tag names.  Group name is optional (e.g. EXIF, IPTC, etc) "
    "but if specified, should be the same as used in `exiftool -G`, e.g. '{exiftool:EXIF:Make}'. "
    "exiftool must be installed in the path to use this template field (https://exiftool.org/).",
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

DATETIME_SUBFIELDS = list(DATETIME_ATTRIBUTES.keys())


@autofile.hookimpl
def get_template_help() -> Iterable:
    text = """
    The `{exiftool}` template uses the third-party exiftool app (https://exiftool.org) to extract metadata from photo and video files.

    It must be used with one or more subfields which are exiftool tags, for example: `{exiftool:EXIF:Make}` for camera make, 
    or `{exiftool:IPTC:Keywords}` for keywords. The exiftool Group name (e.g. `IPTC`) is optional. 

    There are two derived subfields: `created` and `modified` which represent the created date or the modified date, respectively. 
    These subfields are datetime values and you can access the various attributes of the datetime by using an
    attribute name following a period, e.g. `{exiftool:created.year}` for the 4-digit year. 

    The following attributes are supported:

    """
    fields = [["Field", "Description"], *[[k, v] for k, v in FIELDS.items()]]
    attributes = [
        ["Attribute", "Description"],
        *[[k, v] for k, v in DATETIME_ATTRIBUTES.items()],
    ]
    return ["**Photo and Video Files**", fields, text, attributes]


@autofile.hookimpl
def get_template_value(
    filepath: str, field: str, subfield: str, default: List[str]
) -> Optional[List[Optional[str]]]:
    """lookup value for os.stat values for filepath

    Args:
        field: template field to find value for.

    Returns:
        The matching template value (which may be None).
    """
    if "{" + field + "}" not in FIELDS:
        return None

    exiftool = ExifToolCaching(filepath)
    exifdict = exiftool.asdict(normalized=True)
    exifdict_no_groups = exiftool.asdict(tag_groups=False, normalized=True)
    exifdict = exifdict.copy()
    exifdict.update(exifdict_no_groups)

    if not subfield:
        raise ValueError(f"subfield not specified for {field}")

    tag = subfield.lower()
    tag_subfield = None
    if "." in tag:
        tag, tag_subfield = tag.split(".")

    values = []
    if tag == "created":
        date = get_created_date(exiftool)
        if date:
            values = [str(date)]
    elif tag == "modified":
        date = get_modified_date(exiftool)
        if date:
            values = [str(date)]
    elif tag in exifdict:
        values = exifdict[tag]
        values = [values] if not isinstance(values, list) else values
        values = [str(v) for v in values]

        # "(Binary data " below is hack workaround for "(Binary data 0 bytes, use -b option to extract)" error that happens
        # when exporting video with keywords on Photos 5.0 / Catalina
        values = [v for v in values if not v.startswith("(Binary data ")]

    if values and tag_subfield:
        # handle datetime formatting
        if tag not in ["created", "modified"]:
            raise ValueError(
                "date/time formatting can only be used with created or modified subfields"
            )

        if tag_subfield not in DATETIME_SUBFIELDS:
            raise ValueError(f"Invalid value {tag_subfield} for date/time formatter")

        if tag_subfield == "strftime":
            if default:
                try:
                    values = [
                        datetime.datetime.fromisoformat(v).strftime(default[0])
                        for v in values
                    ]
                except:
                    raise ValueError(f"Invalid strftime template: '{default}'")
            else:
                value = None
        else:
            values = [
                getattr(
                    DateTimeFormatter(datetime.datetime.fromisoformat(v)), tag_subfield
                )
                for v in values
            ]

    return values


def get_created_date(exiftool):
    """Get created date from EXIF data or None"""

    data = exiftool.asdict()
    for tag in [
        "Composite:SubSecDateTimeOriginal",
        "Composite:DateTimeCreated",
        "QuickTime:CreationDate",
        "QuickTime:CreateDate",
        "EXIF:DateTimeOriginal",
        "EXIF:CreateDate",
        "IPTC:DateCreated",
        "XMP-xmp:CreateDate",
        "XMP-photoship:DateCreated",
    ]:
        if tag in data:
            return exiftool_date_to_datetime(data[tag])
    else:
        return None


def get_modified_date(exiftool):
    """Get modified date from EXIF data or None"""

    data = exiftool.asdict()
    for tag in [
        "Composite:SubSecModifyDate",
        "EXIF:ModifyDate",
        "QuickTime:ModifyDate",
        "XMP-prism:ModificationDate",
    ]:
        if tag in data:
            return exiftool_date_to_datetime(data[tag])
    else:
        return None


def exiftool_date_to_datetime(date: str) -> datetime.datetime:
    """Convert EXIF date to datetime.datetime"""

    """ exiftool can produce date/times in a variety of formats:
        with TZ offset: "2021:08:01 21:51:33-07:00",
        no TZ offset: "2019:07:27 17:33:28",
        no time: "2019:04:15",
        subsecond, no TZ offset: "2019:04:15 14:40:24.86",
        subsecond, TZ offset: "2019:04:15 14:40:24.86-04:00",
  """

    date_time_formats = [
        "%Y:%m:%d %H:%M:%S%z",
        "%Y:%m:%d %H:%M:%S",
        "%Y:%m:%d %H:%M:%S.%f",
        "%Y:%m:%d %H:%M:%S.%f%z",
        "%Y:%m:%d",
    ]

    for dt_format in date_time_formats:
        try:
            parsed_date = datetime.datetime.strptime(date, dt_format)
        except ValueError as e:
            pass
        else:
            return parsed_date
    else:
        raise ValueError(
            f"Could not parse date format: {date} does not match {date_time_formats}"
        )
