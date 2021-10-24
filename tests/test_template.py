"""Test template system with built-in plugins"""

import locale
import os
import platform
import tempfile

import osxmetadata
import pytest

from autofile.pathlibutil import PathlibUtil
from autofile.renderoptions import RenderOptions
from autofile.template import FileTemplate

PHOTO_FILE = "tests/test_files/pears.jpg"
AUDIO_FILE = "tests/test_files/warm_lights.mp3"

PUNCTUATION = {
    "comma": ",",
    "semicolon": ";",
    "pipe": "|",
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
    [PHOTO_FILE, "{modified.year}", ["2021"]],
    [PHOTO_FILE, "{created.year}", ["2021"]],
    [PHOTO_FILE, "{created.mm}", ["10"]],
    [PHOTO_FILE, "{created.date}", ["2021-10-23"]],
    [
        PHOTO_FILE,
        "{created.year}-{created.yy}-{created.month}-{created.mon}-{created.mm}-{created.dd}-{created.dow}-{created.doy}-{created.hour}-{created.min}-{created.sec}",
        ["2021-21-October-Oct-10-23-Saturday-296-12-53-02"],
    ],
    [PHOTO_FILE, "{created.strftime,%Y-%U}", ["2021-42"]],
    [PHOTO_FILE, "{filepath.name}", ["pears.jpg"]],
    [PHOTO_FILE, "{filepath.stem}", ["pears"]],
    [PHOTO_FILE, "{filepath.parent.name}", ["test_files"]],
    [PHOTO_FILE, "{exiftool:created.year}", ["2021"]],
    [PHOTO_FILE, "{exiftool:Make}", ["Apple"]],
    [PHOTO_FILE, "{,+exiftool:Keywords}", ["fruit,pears"]],
    [PHOTO_FILE, "{exiftool:EXIF:Make}", ["Apple"]],
    [PHOTO_FILE, "{exiftool:IPTC:Keywords contains pears?pears,not_pears}", ["pears"]],
    [PHOTO_FILE, "{mdls:kMDItemKind}", ["JPEG image"]],
    [PHOTO_FILE, "{strip, Foo Bar }", ["Foo Bar"]],
    [PHOTO_FILE, "{uti}", ["public.jpeg"]],
    [AUDIO_FILE, "{mdls:kMDItemContentType}", ["public.mp3"]],
    [AUDIO_FILE, "{audio:title}", ["Warm Lights (ft. Apoxode)"]],
    [AUDIO_FILE, "{audio:artist}", ["Darkroom"]],
    [AUDIO_FILE, "{exiftool:ITPC:Title}", ["_"]],
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
]


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
def test_template_render(data):
    """Test template rendering"""

    # set locale and timezone for testing
    locale.setlocale(locale.LC_ALL, "en_US")
    os.environ["TZ"] = "US/Pacific"

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
