""" plugin example for autofile template system """

from typing import Iterable, List, Optional

from autofile import RenderOptions, hookimpl

# specify which template fields your plugin will provide
FIELDS = {"{foo}": "Returns BAR", "{bar}": "Returns FOO"}


@hookimpl
def get_template_help() -> Iterable:
    """Specify help text for your plugin; will get displayed with autofile --help
    Returns:
        Iterable (e.g. list) of help text as str or list of lists
        str items may be formatted with markdown
        list of lists items can be used for definition lists (e.g. [[key1, value1], [key2, value2]])
    """
    text = """
    This a useless example plugin that returns the text "FOO" or "BAR".

    autofile will correctly format this text for you so don't worry about the spaces preceding each line
    in the docstring block quote. 

    You can use markdown in the docstring to format the text. **This is bold** and *this is italic*.

    - You can also use lists
    - This is another list item

    """
    fields = [["Field", "Description"], *[[k, v] for k, v in FIELDS.items()]]
    return ["**FooBar Fields**", fields, text]


@hookimpl
def get_template_value(
    filepath: str, field: str, subfield: str, default: List[str], options: RenderOptions
) -> Optional[List[Optional[str]]]:
    """lookup value for file dates

    Args:
        filepath: path to the file being processed
        field: template field to find value for
        subfield: the subfield provided, if any (e.g. {field:subfield})
        default: the default value provided to the template, if any (e.g. {field,default})
        options: the render options provided to the template, you likely won't need this

    Returns:
        The matching template value (which may be None) as a list or None if template field is not handled.

    Raises:
        ValueError: if the template is not correctly formatted (e.g. plugin expected a subfield but none provided)
    """
    # if your plugin does not handle a certain field, return None
    if "{" + field + "}" not in FIELDS:
        return None

    if field == "foo":
        return ["BAR"]
    elif field == "bar":
        return ["FOO"]
    else:
        return None
