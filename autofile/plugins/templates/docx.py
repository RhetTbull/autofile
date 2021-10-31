"""Plugin template for autofile to access Microsoft Word .docx file metadata"""

import datetime
import pathlib
from typing import Any, Iterable, List, Optional, Union

import docx

import autofile
from autofile.datetime_formatter import DateTimeFormatter

FIELDS = {
    "{docx}": "Access metadata properties of Microsoft Word document files (.docx); "
    "use in format {docx:SUBFIELD}"
}

SUBFIELDS = {
    "author": "Named ‘creator’ in spec. An entity primarily responsible for making the content of the resource. (Dublin Core)",
    "category": "A categorization of the content of this package. Example values for this property might include: Resume, Letter, Financial Forecast, Proposal, Technical Presentation, and so on. (Open Packaging Conventions)",
    "comments": "Named ‘description’ in spec. An explanation of the content of the resource. Values might include an abstract, table of contents, reference to a graphical representation of content, and a free-text account of the content. (Dublin Core)",
    "content_status": "The status of the content. Values might include “Draft”, “Reviewed”, and “Final”. (Open Packaging Conventions)",
    "created": "Date of creation of the resource; a date/time value. (Dublin Core)",
    "identifier": "An unambiguous reference to the resource within a given context. (Dublin Core)",
    "keywords": "A delimited set of keywords to support searching and indexing. This is typically a list of terms that are not available elsewhere in the properties. (Open Packaging Conventions)",
    "language": "The language of the intellectual content of the resource. (Dublin Core)",
    "last_modified_by": "The user who performed the last modification. The identification is environment-specific. Examples include a name, email address, or employee ID. It is recommended that this value be as concise as possible. (Open Packaging Conventions)",
    "last_printed": "The date and time of the last printing; a date/time value. (Open Packaging Conventions)",
    "modified": "Date on which the resource was changed; a date/time value. (Dublin Core)",
    "revision": "The revision number. This value might indicate the number of saves or revisions, provided the application updates it after each revision. (Open Packaging Conventions)",
    "subject": "The topic of the content of the resource. (Dublin Core)",
    "title": "The name given to the resource. (Dublin Core)",
    "version": "The version designator. This value is set by the user or by the application. (Open Packaging Conventions)",
}

DATETIME_SUBFIELDS = ["created", "modified", "last_printed"]

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
    Access metadata properties of Microsoft Word document files (.docx). Use in format {docx:SUBFIELD}
    where SUBFIELD is one of the following:
 
    """
    text2 = (
        f"If the subfield is a date/time value ({', '.join(DATETIME_SUBFIELDS)}) "
        "the following attributes are available in dot notation (e.g. {docx:created.year}):"
    )

    fields = [["Field", "Description"], *[[k, v] for k, v in FIELDS.items()]]
    subfields = [["Subfield", "Description"], *[[k, v] for k, v in SUBFIELDS.items()]]
    datetime_properties = [
        ["Attribute", "Description"],
        *[[k, v] for k, v in DATETIME_ATTRIBUTES.items()],
    ]
    return [
        "**Microsoft Word Document Fields**",
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
    """lookup value for template docx template fields"""
    if field != "docx":
        return None

    if pathlib.Path(filepath).suffix.lower() != ".docx":
        return [None]

    subfield_parts = subfield.split(".", 1)
    if subfield_parts[0] not in SUBFIELDS:
        raise ValueError(f"Unknown docx subfield {subfield}")

    value = get_docx_property(filepath, subfield_parts[0])

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
    """format values for docx template"""
    if value is None or value == "":
        return None
    elif isinstance(value, datetime.datetime):
        return value.isoformat()
    else:
        return str(value)


def get_docx_property(filepath: str, attribute: str) -> Optional[Union[List, str]]:
    """Return docx core properties attribute or None"""
    doc = docx.Document(filepath)
    core_properties = doc.core_properties
    return getattr(core_properties, attribute, None)
