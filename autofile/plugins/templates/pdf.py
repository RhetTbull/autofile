"""autofile plugin to read PDF metadata"""

import datetime
import logging
import pathlib
import re
from typing import Any, Iterable, List, Optional, Union

from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser

import autofile
from autofile.datetime_formatter import DateTimeFormatter

# pdfminer.six logs a crazy amount of info to logging.INFO so turn off the noise
logging.getLogger("pdfminer").setLevel(logging.WARNING)

FIELDS = {
    "{pdf}": "Access metadata properties of Adobe PDF files (.pdf); "
    "use in format {pdf:SUBFIELD}"
}

SUBFIELDS = {
    "author": "Author of the document.",
    "creator": "The application that created the document.",
    "producer": "The application the produced the PDF (may be different than creator).",
    "created": "Date of creation of the document; a date/time value.",
    "modified": "Date on which the document was changed; a date/time value.",
    "subject": "The topic of the content of the document.",
    "title": "The name given to the document.",
    "keywords": "Keywords associated with the document; a string of delimited words.",
}

SUBFIELD_MAPPING = {
    "author": "Author",
    "creator": "Creator",
    "producer": "Producer",
    "created": "CreationDate",
    "modified": "ModDate",
    "subject": "Subject",
    "title": "Title",
    "keywords": "Keywords",
}

DATETIME_SUBFIELDS = ["created", "modified"]

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
    + "{docx:created.strftime,TEMPLATE} where TEMPLATE is a valid strftime template, e.g. "
    + "{docx:created.strftime,%Y-%U} would result in year-week number of year: '2020-23'. "
    + "If used with no template will return null value. "
    + "See https://strftime.org/ for help on strftime templates.",
}


@autofile.hookimpl
def get_template_help() -> Iterable:
    text = """
    Access metadata properties of Adobe PDF files (.pdf). Use in format {pdf:SUBFIELD}
    where SUBFIELD is one of the following:
 
    """
    text2 = (
        f"If the subfield is a date/time value ({', '.join(DATETIME_SUBFIELDS)}) "
        "the following attributes are available in dot notation (e.g. {pdf:created.year}):"
    )

    fields = [["Field", "Description"], *[[k, v] for k, v in FIELDS.items()]]
    subfields = [["Subfield", "Description"], *[[k, v] for k, v in SUBFIELDS.items()]]
    datetime_properties = [
        ["Attribute", "Description"],
        *[[k, v] for k, v in DATETIME_ATTRIBUTES.items()],
    ]
    return [
        "**Adobe PDF Document Fields**",
        fields,
        text,
        subfields,
        text2,
        datetime_properties,
    ]


@autofile.hookimpl
def get_template_value(
    filepath: str, field: str, subfield: str, default: List[str]
) -> Optional[List[Optional[str]]]:
    """lookup value for template pdf template fields"""
    if field != "pdf":
        return None

    if pathlib.Path(filepath).suffix.lower() != ".pdf":
        return [None]

    subfield_parts = subfield.split(".", 1)
    if subfield_parts[0] not in SUBFIELDS:
        raise ValueError(f"Unknown pdf subfield {subfield}")

    value = get_pdf_property(filepath, subfield_parts[0])

    if len(subfield_parts) == 2 and isinstance(value, datetime.datetime):
        # have a date/time attribute
        dt_attribute = subfield_parts[1]
        if dt_attribute not in DATETIME_ATTRIBUTES:
            raise ValueError(f"Unknown docx datetime attribute {dt_attribute}")
        if dt_attribute == "strftime":
            if default:
                try:
                    value = value.strftime(default[0]) if value else None
                except:
                    raise ValueError(f"Invalid strftime template: '{default}'")
            else:
                value = None
            return [value]
        return [getattr(DateTimeFormatter(value), dt_attribute)]

    return [format_value(value)]


def format_value(value: Any) -> Optional[str]:
    """format values for pdf template"""
    if not value:
        return None
    elif isinstance(value, datetime.datetime):
        return value.isoformat()
    else:
        return str(value)


def get_pdf_property(
    filepath: str, subfield: str
) -> Optional[Union[str, datetime.datetime]]:
    """get pdf property"""
    metadata = get_pdf_metadata_info(filepath)
    try:
        subfield_mapping = SUBFIELD_MAPPING[subfield]
    except KeyError:
        raise ValueError(f"Unknown pdf subfield {subfield}")
    value = metadata.get(subfield_mapping, None)
    if not value:
        return None

    if subfield in DATETIME_SUBFIELDS:
        return pdf_date_to_datetime(decode_pdf_field(value))
    return decode_pdf_field(value)


def decode_pdf_field(field: Any) -> str:
    """decode pdf metadata field from binary unicode to str"""
    # XMP Spec says that PDF metadata fields are encoded in UTF-8, but
    # that is not always the case so this tries various encodings to find one that works
    for encoding in ("utf-8", "utf-16", "utf-32"):
        try:
            value = field.decode(encoding)
        except UnicodeDecodeError:
            pass
        else:
            return value
    return field.decode("utf-8", errors="ignore")


def get_pdf_metadata_info(pdfpath: str) -> dict:
    """
    Get the metadata info from a pdf file
    """
    with open(pdfpath, "rb") as fp:
        parser = PDFParser(fp)
        doc = PDFDocument(parser)
        return doc.info[0] if doc.info else {}


def pdf_date_to_datetime(date_str: str) -> datetime.datetime:
    """
    Convert a pdf date such as "D:20120321183444+07'00'" into a usable datetime
    http://www.verypdf.com/pdfinfoeditor/pdf-date-format.htm
    (D:YYYYMMDDHHmmSSOHH'mm')
    From https://stackoverflow.com/questions/16503075/convert-creationtime-of-pdf-to-a-readable-format-in-python
    :param date_str: pdf date string
    :return: datetime object
    """

    pdf_date_pattern = re.compile(
        "".join(
            [
                r"(D:)?",
                r"(?P<year>\d\d\d\d)",
                r"(?P<month>\d\d)",
                r"(?P<day>\d\d)",
                r"(?P<hour>\d\d)",
                r"(?P<minute>\d\d)",
                r"(?P<second>\d\d)",
                r"(?P<tz_offset>[+-zZ])?",
                r"(?P<tz_hour>\d\d)?",
                r"'?(?P<tz_minute>\d\d)?'?",
            ]
        )
    )

    match = re.match(pdf_date_pattern, date_str)
    if match:
        # date_info is the dict from the match, dt_info is dict to pass to datetime.datetime as **kwargs
        date_info = match.groupdict()
        dt_info = {
            k: int(date_info[k])
            for k in ["year", "month", "day", "hour", "minute", "second"]
        }

        for k, v in date_info.items():  # transform values
            if v is None:
                pass
            elif k == "tz_offset":
                date_info[k] = v.lower()  # so we can treat Z as z
            else:
                date_info[k] = int(v)

        if date_info["tz_offset"] in ("z", None):  # UTC
            dt_info["tzinfo"] = datetime.timezone.utc
        else:
            multiplier = 1 if date_info["tz_offset"] == "+" else -1
            dt_info["tzinfo"] = datetime.timezone(
                datetime.timedelta(
                    seconds=float(
                        multiplier
                        * (3600 * date_info["tz_hour"] + 60 * date_info["tz_minute"]),
                    )
                )
            )

        return datetime.datetime(**dt_info)

    raise ValueError(f"Invalid date string: {date_str}")
