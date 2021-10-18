from typing import Dict, List, Optional

from pluggy import HookimplMarker, HookspecMarker

from .constants import APP_NAME
from .renderoptions import RenderOptions

hookspec = HookspecMarker(APP_NAME)
hookimpl = HookimplMarker(APP_NAME)


@hookspec(firstresult=True)
def get_template_value(
    filepath: str, field: str, subfield: str, default: str, options: RenderOptions
) -> Optional[List[Optional[str]]]:
    """Called by template.py to get template value for custom template

    Return: None if field is not handled by this plugin otherwise list of str values"""


@hookspec
def get_template_help() -> Dict:
    """Return dictionary of {field: help}"""
