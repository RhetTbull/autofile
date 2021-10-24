""" plugin for autofile template: punctuation characters"""

from typing import Iterable, List, Optional

import autofile

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

FIELDS = {
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


@autofile.hookimpl
def get_template_help() -> Iterable:
    text = """
    Within the template system, many punctuation characters have special meaning, e.g. `{}` indicates a template field 
    and this means that some punctuation characters cannot be inserted into the template. 
    Thus, if you want to insert punctuation into the rendered template value, you can use these punctuation fields to do so. 
    For example, `{openbrace}value{closebrace}` will render to `{value}`.
    """
    fields = [["Field", "Description"], *[[k, v] for k, v in FIELDS.items()]]
    return ["**Punctuation Fields**", fields, text]


@autofile.hookimpl
def get_template_value(
    filepath: str, field: str, subfield: str, default: List[str]
) -> Optional[List[Optional[str]]]:
    """Called by template.py to get template value for custom template"""
    value = PUNCTUATION.get(field)
    return [value] if value else None
