""" Custom template system for autofile """

import importlib
import locale
import pathlib
from textwrap import dedent
from typing import Any, Dict, List, Optional, Tuple, Union

import pluggy
from textx import TextXSyntaxError, metamodel_from_file

from . import hookspecs
from ._version import __version__
from .constants import APP_NAME
from .mtlparser import FORMAT_FIELDS, PUNCTUATION_FIELDS, MTLParser
from .path_utils import sanitize_dirname, sanitize_filename, sanitize_pathpart
from .pathlibutil import PathlibUtil
from .renderoptions import RenderOptions


class UnknownFieldError(Exception):
    """Raised when a field is not known"""

    pass


class SyntaxError(Exception):
    """Raised when template engine cannot parse the template string"""

    pass


DEFAULT_PLUGINS = (
    "autofile.plugins.templates.docx",
    "autofile.plugins.templates.pdf",
    "autofile.plugins.templates.exiftool",
    "autofile.plugins.templates.audio",
    "autofile.plugins.templates.uti",
    "autofile.plugins.templates.finder",
    "autofile.plugins.templates.mdls",
    "autofile.plugins.templates.filepath",
    "autofile.plugins.templates.filedates",
    "autofile.plugins.templates.filestat",
)


def get_plugin_manager():
    pm = pluggy.PluginManager(APP_NAME)
    pm.add_hookspecs(hookspecs)
    pm.load_setuptools_entrypoints(APP_NAME)
    return pm


PM = get_plugin_manager()

# Load default plugins
for plugin in DEFAULT_PLUGINS:
    mod = importlib.import_module(plugin)
    PM.register(mod, plugin)

# ensure locale set to user's locale
locale.setlocale(locale.LC_ALL, "")


class FileTemplate:
    """FileTemplate class to render a template string from a file and it's associated metadata"""

    def __init__(self, filepath: Union[str, PathlibUtil, pathlib.Path]):
        """Inits FileTemplate class with filepath and exiftool_path"""

        if isinstance(filepath, str):
            filepath = PathlibUtil(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File {filepath} does not exist")

        self.filepath = str(filepath)
        self.hook = PM.hook

        # initialize render options
        # this will be done in render() but for testing, some of the lookup functions are called directly
        options = RenderOptions()
        self.options = options
        self.tag = options.tag
        self.group, self.tagname = "", ""
        self.inplace_sep = options.inplace_sep
        self.none_str = options.none_str
        self.expand_inplace = options.expand_inplace
        self.filename = options.filename
        self.dirname = options.dirname
        self.strip = options.strip
        self.quote = options.quote
        self.dest_path = options.dest_path

    def get_field_value(self, field, subfield, default):
        """Get the value of a field"""
        return self.hook.get_template_value(
            filepath=self.filepath,
            field=field,
            subfield=subfield,
            default=default,
            options=self.options,
        )

    def render(
        self,
        template: str,
        options: Optional[RenderOptions] = None,
    ):
        """Render a filename or directory template

        Args:
            template: str template
            options: a RenderOptions instance

        Returns:
            [rendered_strings]: list of rendered strings
        """

        if type(template) is not str:
            raise TypeError(f"template must be type str, not {type(template)}")

        options = options or RenderOptions()
        self.options = options
        self.tag = options.tag
        self.inplace_sep = options.inplace_sep
        self.none_str = options.none_str
        self.expand_inplace = options.expand_inplace
        self.filename = options.filename
        self.dirname = options.dirname
        self.strip = options.strip
        self.dest_path = options.dest_path
        self.quote = options.quote
        self.dest_path = options.dest_path

        sanitize_value = (
            sanitize_dirname
            if options.dirname
            else sanitize_pathpart
            if options.filename
            else None
        )
        sanitize = sanitize_filename if options.filename else None

        parser = MTLParser(
            get_field_values=self.get_field_value,
            sanitize=sanitize,
            sanitize_value=sanitize_value,
            expand_inplace=options.expand_inplace,
            inplace_sep=options.inplace_sep,
            none_str=options.none_str,
        )
        rendered = parser.render(template)
        if options.strip:
            rendered = [r.strip() for r in rendered]
        return rendered


def get_template_help() -> List[Any]:
    """Return help for template system as list of markdown strings or lists of lists"""
    # TODO: would be better to use importlib.abc.ResourceReader but I can't find a single example of how to do this
    help_file = pathlib.Path(__file__).parent / "filetemplate.md"
    with open(help_file, "r") as fd:
        md = [fd.read()]

    # add help for built-in punctuation fields
    punctuation_help = """
    Within the template system, many punctuation characters have special meaning, e.g. `{}` indicates a template field 
    and this means that some punctuation characters cannot be inserted into the template. 
    Thus, if you want to insert punctuation into the rendered template value, you can use these punctuation fields to do so. 
    For example, `{openbrace}value{closebrace}` will render to `{value}`.
    """
    punctuation_fields = [
        ["Field", "Description"],
        *[[k, v[0]] for k, v in PUNCTUATION_FIELDS.items()],
    ]
    md.append("**Punctuation Fields**")
    md.append(punctuation_fields)
    md.append("\n" + dedent(punctuation_help).strip())

    # add help for built-in format fields
    format_help = """
    The `{strip}` and `{format}` fields are used to format strings. 
    `{strip,TEMPLATE}` strips whitespace from TEMPLATE. 
    For example, `{strip,{exiftool:Title}}` will strip any excess whitespace from the title of an image file. 

    `{format:TYPE:FORMAT,TEMPLATE}` formats TEMPLATE using python string formatting codes. 
    For example: 
    
    - `{format:int:02d,{audio:track}}` will format the track number of an audio file to two digits with leading zeros. 
    - `{format:str:-^30,{audio.title}}` will center the title of an audio file and pad it to 30 characters with '-'.

    TYPE must be one of 'int', 'float', or 'str'. 

    FORMAT may be a string or an variable. A variable may be helpful when you need to use a character in the format string that 
    would otherwise not be allowed. For example, to use a comma separator, you could do this:
    
    `{var:commaformat,{comma}}{format:int:%commaformat,{created.year}}` which transforms "2021" to "2,021"
 
    See https://docs.python.org/3.7/library/string.html#formatspec for more information on valid FORMAT values.
    """
    md.append("**String Formatting Fields**")
    format_fields = [
        ["Field", "Description"],
        *[[k, v[0]] for k, v in FORMAT_FIELDS.items()],
    ]
    md.append(format_fields)
    md.append("\n" + dedent(format_help).strip())

    # process help from plugins
    help_texts = PM.hook.get_template_help()
    for help_text in help_texts:
        # help_text is an iterable of str, dicts, or lists or lists
        for item in help_text:
            if type(item) == str:
                # format str as it might be a docstring
                md.append("\n" + dedent(item).strip())
            elif isinstance(item, (list, tuple)):
                md.append(item)
            else:
                raise ValueError(f"Unhandled help item: {item}")
    return md
