"""template plugin for audio files for autofile"""

""" Works on the following audio formats:
    Wave/RIFF
    OGG
    OPUS
    FLAC
    WMA
    MP4/M4A/M4B
    AIFF/AIFF-C
"""

from typing import Iterable, List, Optional

from tinytag import TinyTag, TinyTagException

import autofile

FIELDS = {
    "{audio}": "Use in form '{audio:TAG}'; Returns tag value for various audio types include mp3, "
}

SUBFIELDS = {
    "album": "album as string",
    "albumartist": "album artist as string",
    "artist": "artist name as string",
    "audio_offset": "number of bytes before audio data begins",
    "bitrate": "bitrate in kBits/s",
    "comment": "file comment as string",
    "composer": "composer as string",
    "disc": "disc number",
    "disc_total": "the total number of discs",
    "duration": "duration of the song in seconds",
    "filesize": "file size in bytes",
    "genre": "genre as string",
    "samplerate": "samples per second",
    "title": "title of the song",
    "track": "track number as string",
    "track_total": "total number of tracks as string",
    "year": "year or data as string",
}


@autofile.hookimpl
def get_template_help() -> Iterable:
    text = """
    The `{audio}` field provides access to audio-file related tags for audio files. The following formats are supported:

    - MP3 (ID3 v1, v1.1, v2.2, v2.3+)
    - Wave/RIFF
    - OGG
    - OPUS
    - FLAC
    - WMA
    - MP4/M4A/M4B
    - AIFF/AIFF-C

    The `{audio}` field must be used with one or more the following subfields in the form: `{audio:SUBFIELD}`, 
    for example: `{audio:title}` or `{audio:artist}`. 
    """

    fields = [["Field", "Description"], *[[k, v] for k, v in FIELDS.items()]]
    subfields = [["Subfield", "Description"], *[[k, v] for k, v in SUBFIELDS.items()]]
    return ["**Audio Files**", fields, text, subfields]


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
    if "{" + field + "}" not in FIELDS:
        return None

    try:
        tag = TinyTag.get(filepath)
        vals = []
        if field == "audio":
            if subfield is None:
                raise ValueError("subfield must be specified for audio field")
            if subfield not in SUBFIELDS:
                raise ValueError(f"Unknown audio subfield: {subfield}")
            vals = getattr(tag, subfield)
        return [vals]
    except TinyTagException as e:
        autofile.cli.print_warning(
            f"Error reading tag {field}:{subfield} for file {filepath}: {e}"
        )
        return [None]
