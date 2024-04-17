""""Make test documents for autofile docx plugin"""

import datetime
from dataclasses import dataclass
from typing import List, Optional

import docx

PROPERTIES = {
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


@dataclass
class CoreProperties:
    """Class representing docx Core Properties"""

    author: Optional[str] = None
    category: Optional[str] = None
    comments: Optional[str] = None
    content_status: Optional[str] = None
    created: Optional[datetime.datetime] = None
    identifier: Optional[str] = None
    keywords: Optional[str] = None
    language: Optional[str] = None
    last_modified_by: Optional[str] = None
    last_printed: Optional[datetime.datetime] = None
    modified: Optional[datetime.datetime] = None
    revision: Optional[int] = None
    subject: Optional[str] = None
    title: Optional[str] = None
    version: Optional[str] = None


def make_document(filepath: str, core_properties: CoreProperties):
    """Make a docx document with the given core properties"""
    doc = docx.Document()
    properties = doc.core_properties
    for prop in PROPERTIES:
        value = getattr(core_properties, prop)
        if value is not None:
            setattr(properties, prop, value)
    doc.save(filepath)


def main():
    """Create test documents for autofile"""

    # first create document with all metadata filled in
    properties = CoreProperties(
        author="Rhet Turnbull",
        category="test",
        comments="This is a comment",
        content_status="Draft",
        created=datetime.datetime(2021, 10, 30, 8, 15, 0),
        identifier="test",
        keywords="test, test2",
        language="en-US",
        last_modified_by="Rhet Turnbull",
        last_printed=datetime.datetime(2021, 10, 30, 21, 15, 0),
        modified=datetime.datetime(2021, 10, 30, 22, 15, 0),
        revision=42,
        subject="test",
        title="Test Document",
        version="1.0",
    )
    make_document("test1_data.docx", properties)

    # now create document with some metadata missing
    properties = CoreProperties(
        author="Rhet Turnbull",
        category="",
        comments="This is a comment",
        content_status="",
        created=datetime.datetime(2021, 10, 30, 8, 15, 0),
        identifier="",
        keywords="",
        language="",
        last_modified_by="",
        last_printed=datetime.datetime(2021, 10, 30, 21, 15, 0),
        modified=datetime.datetime(2021, 10, 30, 22, 15, 0),
        revision=1,
        subject="",
        title="",
        version="",
    )
    make_document("test2_no_data.docx", properties)


if __name__ == "__main__":
    main()
