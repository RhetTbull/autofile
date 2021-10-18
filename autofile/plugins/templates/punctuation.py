""" plugin for autofile template: punctuation characters"""

from typing import Dict, List, Optional

from autofile import hookimpl
from autofile.renderoptions import RenderOptions

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


@hookimpl
def get_template_help() -> Dict:
    return {
        "{comma}": "A comma: ','",
        "{semicolon}": "A semicolon: ';'",
        "{questionmark}": "A question mark: '?'",
        "{pipe}": "A vertical pipe: '|'",
        "{openbrace}": "An open brace: '{'",
        "{closebrace}": "A close brace: '}'",
        "{openparens}": "An open parentheses: '('",
        "{closeparens}": "A close parentheses: ')'",
        "{openbracket}": "An open bracket: '['",
        "{closebracket}": "A close bracket: ']'",
        "{newline}": r"A newline: '\n'",
        "{lf}": r"A line feed: '\n', alias for {newline}",
        "{cr}": r"A carriage return: '\r'",
        "{crlf}": r"a carriage return + line feed: '\r\n'",
    }


@hookimpl
def get_template_value(
    filepath: str, field: str, subfield: str, default: str, options: RenderOptions
) -> Optional[List[Optional[str]]]:
    """Called by template.py to get template value for custom template"""
    value = PUNCTUATION.get(field)
    return [value] if value else None
