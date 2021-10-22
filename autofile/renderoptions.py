"""RenderOptions class for template system"""

from dataclasses import dataclass
from typing import Optional

from .constants import INPLACE_DEFAULT, NONE_STR_DEFAULT, NONE_STR_SENTINEL


@dataclass
class RenderOptions:
    """Options for PhotoTemplate.render

    tag: tag name being processed
    none_str: str to use default for None values
    path_sep: optional string to use as path separator, default is os.path.sep
    expand_inplace: expand multi-valued substitutions in-place as a single string
        instead of returning individual strings
    inplace_sep: optional string to use as separator between multi-valued keywords
    with expand_inplace; default is ','
    filename: if True, template output will be sanitized to produce valid file name
    dirname: if True, template output will be sanitized to produce valid directory name
    strip: if True, strips leading/trailing whitespace from rendered templates
    dest_path: set to the destination path of the file (for use by {function} template)
    quote: quote path templates for execution in the shell
    """

    tag: Optional[str] = None
    none_str: str = NONE_STR_DEFAULT
    expand_inplace: bool = False
    inplace_sep: Optional[str] = INPLACE_DEFAULT
    filename: bool = False
    dirname: bool = False
    strip: bool = False
    dest_path: Optional[str] = None
    quote: bool = False
