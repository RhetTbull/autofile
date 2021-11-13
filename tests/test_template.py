"""Test template system with built-in plugins"""

import locale
import os
import platform
import tempfile

import osxmetadata
import pytest
from freezegun import freeze_time

import autofile
from autofile.pathlibutil import PathlibUtil
from autofile.renderoptions import RenderOptions
from autofile.filetemplate import FileTemplate, SyntaxError

PHOTO_FILE = "tests/test_files/pears.jpg"
AUDIO_FILE = "tests/test_files/warm_lights.mp3"
DOC_FILE_1 = "tests/test_files/test1_data.docx"
DOC_FILE_2 = "tests/test_files/test2_no_data.docx"
PDF_FILE_1 = "tests/test_files/test_pdf.pdf"
PDF_FILE_2 = "tests/test_files/test_pdf_blank_metadata.pdf"

PUNCTUATION = {
    "comma": ",",
    "semicolon": ";",
    "pipe": "|",
    "percent": "%",
    "openbrace": "{",
    "closebrace": "}",
    "openparens": "(",
    "closeparens": ")",
    "openbracket": "[",
    "closebracket": "]",
    "questionmark": "?",
    "newline": "\n",
    "lf": "\n",
    "cr": "\r",
    "crlf": "\r\n",
}

TEST_DATA = [
    # dates and paths
    [PHOTO_FILE, "{modified.year}", ["2021"]],
    [PHOTO_FILE, "{created.year}", ["2021"]],
    [PHOTO_FILE, "{created.mm}", ["11"]],
    [PHOTO_FILE, "{created.date}", ["2021-11-03"]],
    [
        PHOTO_FILE,
        "{created.year}-{created.yy}-{created.month}-{created.mon}-{created.mm}-{created.dd}-{created.dow}-{created.doy}-{created.hour}-{created.min}-{created.sec}",
        ["2021-21-November-Nov-11-03-Wednesday-307-05-33-33"],
    ],
    [PHOTO_FILE, "{created.strftime,%Y-%U}", ["2021-44"]],
    [PHOTO_FILE, "{filepath.name}", ["pears.jpg"]],
    [PHOTO_FILE, "{filepath.stem}", ["pears"]],
    [PHOTO_FILE, "{filepath.parent.name}", ["test_files"]],
    # exiftool
    [PHOTO_FILE, "{exiftool:created.year}", ["2021"]],
    [PHOTO_FILE, "{exiftool:Make}", ["Apple"]],
    [PHOTO_FILE, "{,+exiftool:Keywords}", ["fruit,pears"]],
    [PHOTO_FILE, "{exiftool:EXIF:Make}", ["Apple"]],
    [PHOTO_FILE, "{exiftool:IPTC:Keywords contains pears?pears,not_pears}", ["pears"]],
    # mdls
    [PHOTO_FILE, "{mdls:kMDItemKind}", ["JPEG image"]],
    [AUDIO_FILE, "{mdls:kMDItemContentType}", ["public.mp3"]],
    # strip
    [PHOTO_FILE, "{strip, Foo Bar }", ["Foo Bar"]],
    # uti
    [PHOTO_FILE, "{uti}", ["public.jpeg"]],
    # mp3 file
    [AUDIO_FILE, "{audio:title}", ["Warm Lights (ft. Apoxode)"]],
    [AUDIO_FILE, "{audio:artist}", ["Darkroom"]],
    [AUDIO_FILE, "{exiftool:ITPC:Title}", ["_"]],
    # filters
    [PHOTO_FILE, "{filepath.stem|lower}", ["pears"]],
    [PHOTO_FILE, "{filepath.stem|upper}", ["PEARS"]],
    [PHOTO_FILE, "{filepath.stem|strip}", ["pears"]],
    [PHOTO_FILE, "{filepath.stem|braces}", ["{pears}"]],
    [PHOTO_FILE, "{filepath.stem|braces}", ["{pears}"]],
    [PHOTO_FILE, "{filepath.stem|parens}", ["(pears)"]],
    [PHOTO_FILE, "{filepath.stem|brackets}", ["[pears]"]],
    [PHOTO_FILE, "{filepath.stem[e,E|a,A]}", ["pEArs"]],
    [AUDIO_FILE, "{audio:title|titlecase}", ["Warm Lights (Ft. Apoxode)"]],
    [AUDIO_FILE, "{audio:title|capitalize}", ["Warm lights (ft. apoxode)"]],
    # docx
    [PHOTO_FILE, "{docx:author}", ["_"]],
    [DOC_FILE_1, "{docx:author}", ["Rhet Turnbull"]],
    [DOC_FILE_1, "{docx:category}", ["test"]],
    [DOC_FILE_1, "{docx:comments}", ["This is a comment"]],
    [DOC_FILE_1, "{docx:content_status}", ["Draft"]],
    [DOC_FILE_1, "{docx:created}", ["2021-10-30T08:15:00"]],
    [DOC_FILE_1, "{docx:created.year}", ["2021"]],
    [DOC_FILE_1, "{docx:identifier}", ["test"]],
    [DOC_FILE_1, "{docx:keywords}", ["test, test2"]],
    [DOC_FILE_1, "{docx:language}", ["en-US"]],
    [DOC_FILE_1, "{docx:last_modified_by}", ["Rhet Turnbull"]],
    [DOC_FILE_1, "{docx:last_printed}", ["2021-10-30T21:15:00"]],
    [DOC_FILE_1, "{docx:modified}", ["2021-10-30T22:15:00"]],
    [DOC_FILE_1, "{docx:modified.mm}", ["10"]],
    [DOC_FILE_1, "{docx:revision}", ["42"]],
    [DOC_FILE_1, "{docx:subject}", ["test"]],
    [DOC_FILE_1, "{docx:title}", ["Test Document"]],
    [DOC_FILE_1, "{docx:version}", ["1.0"]],
    # docx with blank metadata
    [DOC_FILE_2, "{docx:author}", ["Rhet Turnbull"]],
    [DOC_FILE_2, "{docx:category}", ["_"]],
    [DOC_FILE_2, "{docx:comments}", ["This is a comment"]],
    [DOC_FILE_2, "{docx:content_status}", ["_"]],
    [DOC_FILE_2, "{docx:created}", ["2021-10-30T08:15:00"]],
    [DOC_FILE_2, "{docx:created.year}", ["2021"]],
    [DOC_FILE_2, "{docx:identifier}", ["_"]],
    [DOC_FILE_2, "{docx:keywords}", ["_"]],
    [DOC_FILE_2, "{docx:language}", ["_"]],
    [DOC_FILE_2, "{docx:last_modified_by}", ["_"]],
    [DOC_FILE_1, "{docx:last_printed}", ["2021-10-30T21:15:00"]],
    [DOC_FILE_1, "{docx:modified}", ["2021-10-30T22:15:00"]],
    [DOC_FILE_1, "{docx:modified.mm}", ["10"]],
    [DOC_FILE_2, "{docx:revision}", ["1"]],
    [DOC_FILE_2, "{docx:subject}", ["_"]],
    [DOC_FILE_2, "{docx:title}", ["_"]],
    [DOC_FILE_2, "{docx:version}", ["_"]],
    # split filter
    [DOC_FILE_1, "{docx:keywords|split(,)|strip}", ["test", "test2"]],
    # chop, chomp
    [DOC_FILE_1, "{docx:author|chop(2)|lower}", ["rhet turnbu"]],
    [DOC_FILE_1, "{docx:author|lower|chop(2)}", ["rhet turnbu"]],
    [DOC_FILE_1, "{docx:author|chomp(1)|upper}", ["HET TURNBULL"]],
    [DOC_FILE_1, "{docx:author|upper|chomp(1)}", ["HET TURNBULL"]],
    [DOC_FILE_1, "{docx:author|upper|chomp(1)|chop(1)|split( )}", ["HET", "TURNBUL"]],
    [DOC_FILE_1, "{docx:author|chomp(0)|chomp(0)}", ["Rhet Turnbull"]],
    # autosplit
    [DOC_FILE_1, "{docx:identifier|autosplit}", ["test"]],
    [DOC_FILE_1, "{docx:keywords|autosplit}", ["test", "test2"]],
    # variables
    [DOC_FILE_1, "{var:foo,BAR}{%foo}", ["BAR"]],
    [DOC_FILE_1, "{docx:author[ ,%%]}", ["Rhet%Turnbull"]],  # test escape of %
    [DOC_FILE_1, "{docx:author[ ,%%%%]}", ["Rhet%%Turnbull"]],  # test escape of %
    [
        DOC_FILE_1,
        "{docx:author contains Rhet?{docx:author}{percent},{docx:author}}",
        ["Rhet Turnbull%"],
    ],
    [DOC_FILE_1, "{var:bar,FOO}{var:foo,BAR}{%foo[%foo,%bar]}", ["FOO"]],
    [DOC_FILE_1, "{var:space, }{docx:author|split(%space)}", ["Rhet", "Turnbull"]],
    [DOC_FILE_1, "{var:pipe,|}{docx:author[ ,%pipe]}", ["Rhet|Turnbull"]],
    [
        DOC_FILE_1,
        "{var:name,Rhet}{docx:author contains {%name}?{%name},Not-{%name}}",
        ["Rhet"],
    ],
    [
        DOC_FILE_1,
        "{var:name,Rhet}{docx:author not contains {%name}?{%name},Not-{%name}}",
        ["Not-Rhet"],
    ],
    # operators
    [DOC_FILE_1, "{docx:author contains Rhet?YES,NO}", ["YES"]],
    [DOC_FILE_1, "{docx:author not contains Rhet?YES,NO}", ["NO"]],
    [DOC_FILE_1, "{docx:author matches Rhet Turnbull?YES,NO}", ["YES"]],
    [DOC_FILE_1, "{docx:author matches John Doe?YES,NO}", ["NO"]],
    [DOC_FILE_1, "{docx:author not matches John Doe?YES,NO}", ["YES"]],
    [DOC_FILE_1, "{docx:author startswith Rhet?YES,NO}", ["YES"]],
    [DOC_FILE_1, "{docx:author startswith John?YES,NO}", ["NO"]],
    [DOC_FILE_1, "{docx:author not startswith John?YES,NO}", ["YES"]],
    [DOC_FILE_1, "{docx:author endswith Turnbull?YES,NO}", ["YES"]],
    [DOC_FILE_1, "{docx:author endswith Rhet?YES,NO}", ["NO"]],
    [DOC_FILE_1, "{docx:author not endswith Rhet?YES,NO}", ["YES"]],
    [AUDIO_FILE, "{audio:bitrate <= 320?YES,NO}", ["YES"]],
    [AUDIO_FILE, "{audio:bitrate <= 0?YES,NO}", ["NO"]],
    [AUDIO_FILE, "{audio:bitrate >= 320?YES,NO}", ["YES"]],
    [AUDIO_FILE, "{audio:bitrate >= 540?YES,NO}", ["NO"]],
    [AUDIO_FILE, "{audio:bitrate < 320?YES,NO}", ["NO"]],
    [AUDIO_FILE, "{audio:bitrate not < 320?YES,NO}", ["YES"]],
    [AUDIO_FILE, "{audio:bitrate > 320?YES,NO}", ["NO"]],
    [AUDIO_FILE, "{audio:bitrate > 0?YES,NO}", ["YES"]],
    [AUDIO_FILE, "{audio:bitrate == 320?YES,NO}", ["YES"]],
    [AUDIO_FILE, "{audio:bitrate == 0?YES,NO}", ["NO"]],
    [AUDIO_FILE, "{audio:bitrate != 0?YES,NO}", ["YES"]],
    [AUDIO_FILE, "{audio:bitrate != 320?YES,NO}", ["NO"]],
    [PHOTO_FILE, "{exiftool:IPTC:Keywords contains pears?YES,NO}", ["YES"]],
    [PHOTO_FILE, "{exiftool:IPTC:Keywords not contains pears?YES,NO}", ["NO"]],
    [
        PHOTO_FILE,
        "{exiftool:IPTC:Keywords startswith pea?YES,NO}",
        ["YES"],
    ],  # match pears
    [
        PHOTO_FILE,
        "{exiftool:IPTC:Keywords endswith uit?YES,NO}",
        ["YES"],
    ],  # match fruit
    # pdf files
    [PDF_FILE_1, "{pdf:title}", ["Test Document"]],
    [PDF_FILE_1, "{pdf:subject}", ["Testing"]],
    [PDF_FILE_1, "{pdf:author}", ["Rhet Turnbull"]],
    [
        PDF_FILE_1,
        "{pdf:producer}",
        ["macOS Version 10.15.7 (Build 19H1419) Quartz PDFContext"],
    ],
    [PDF_FILE_1, "{pdf:creator}", ["TextEdit"]],
    [PDF_FILE_1, "{pdf:created}", ["2021-11-07T14:50:06+00:00"]],
    [PDF_FILE_1, "{pdf:modified}", ["2021-11-07T14:50:06+00:00"]],
    [PDF_FILE_1, "{pdf:keywords}", ["test, pdf, document"]],
    [PDF_FILE_1, "{pdf:keywords|autosplit}", ["test", "pdf", "document"]],
    [PDF_FILE_1, "{pdf:created.year}", ["2021"]],
    [PDF_FILE_1, "{pdf:modified.mm}", ["11"]],
    [PDF_FILE_2, "{pdf:author}", ["_"]],
]


@pytest.fixture
def setlocale():
    # set locale and timezone for testing
    locale.setlocale(locale.LC_ALL, "en_US")
    tz = os.environ.get("TZ")
    os.environ["TZ"] = "US/Pacific"
    yield
    if tz:
        os.environ["TZ"] = tz


def test_template_render_punctuation():
    """Test that punctuation is rendered correctly"""
    options = RenderOptions()
    for key, value in PUNCTUATION.items():
        assert FileTemplate(PHOTO_FILE).render("{" + key + "}", options=options)[0] == [
            value
        ]


@pytest.mark.skipif(
    platform.node() != "Rhets-MacBook-Pro.local",
    reason="Only runs on author's personal machine",
)
def test_template_render_filestat():
    """Test for filestat plugin"""
    options = RenderOptions()
    template = FileTemplate(PHOTO_FILE)
    assert template.render("{size}-{uid}-{gid}-{user}-{group}", options=options)[0] == [
        "2771656-501-20-rhet-staff"
    ]


@pytest.mark.parametrize("data", TEST_DATA)
def test_template_render(data, setlocale):
    """Test template rendering"""

    template = FileTemplate(data[0])
    result, _ = template.render(data[1], options=RenderOptions())
    assert result == data[2]


def test_template_finder():
    """Test {finder} template"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = PathlibUtil(PHOTO_FILE).copy_to(tmpdir)
        md = osxmetadata.OSXMetaData(test_file)
        md.tags = [osxmetadata.Tag("Foo")]
        md.findercomment = "FizzBuzz"

        template = FileTemplate(test_file)
        rendered, _ = template.render(
            "{finder:tags}-{finder:comment}", options=RenderOptions()
        )
        assert rendered == ["Foo-FizzBuzz"]


@freeze_time("2021-10-29T05:39:00.028590-07:00")
def test_template_filedates_today(setlocale):
    """Test {today}"""
    autofile.plugins.templates.filedates.TODAY = None
    template = FileTemplate(PHOTO_FILE)
    rendered, _ = template.render("{today}", options=RenderOptions())
    assert rendered == ["2021-10-29T05:39:00.028590-07:00"]
    rendered, _ = template.render("{today}", options=RenderOptions())
    assert rendered == ["2021-10-29T05:39:00.028590-07:00"]


@freeze_time("2021-10-29T05:39:00.012345-07:00")
def test_template_filedates_now(setlocale):
    """Test {now}"""
    autofile.plugins.templates.filedates.TODAY = None
    template = FileTemplate(PHOTO_FILE)
    rendered, _ = template.render("{now}", options=RenderOptions())
    assert rendered == ["2021-10-29T05:39:00.012345-07:00"]
    rendered, _ = template.render("{now}", options=RenderOptions())
    assert rendered == ["2021-10-29T05:39:00.012345-07:00"]


def test_template_var_error():
    """Test template var error"""
    template = FileTemplate(PHOTO_FILE)
    with pytest.raises(SyntaxError):
        template.render("{var:foo}", options=RenderOptions())
    with pytest.raises(SyntaxError):
        template.render("{%bar}", options=RenderOptions())
