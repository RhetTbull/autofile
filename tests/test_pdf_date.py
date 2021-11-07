"""Test date conversions from pdf plugin"""

import datetime

import pytest

from autofile.plugins.templates.pdf import pdf_date_to_datetime

TEST_DATA = [
    ["D:19981223195200-08'00'", "1998-12-23 19:52:00-08:00"],
    ["D:20140327195230+05'00'", "2014-03-27 19:52:30+05:00"],
    ["D:20211101061600", "2021-11-01 06:16:00+00:00"],
    ["D:20211101061600Z", "2021-11-01 06:16:00+00:00"],
]


@pytest.mark.parametrize("data", TEST_DATA)
def test_pdf_date_to_datetime(data):
    """Test pdf_date_to_datetime"""
    pdf_date, expected_datetime = data
    assert pdf_date_to_datetime(pdf_date) == datetime.datetime.strptime(
        expected_datetime, "%Y-%m-%d %H:%M:%S%z"
    )
