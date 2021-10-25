""" Custom template system for autofile """

import importlib
import locale
import pathlib
import re
import shlex
from textwrap import dedent
from typing import Dict, List, Optional, Tuple, Union

import pluggy
from textx import TextXSyntaxError, metamodel_from_file

from . import hookspecs
from ._version import __version__
from .constants import APP_NAME
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
    "autofile.plugins.templates.punctuation",
    "autofile.plugins.templates.exiftool",
    "autofile.plugins.templates.audio",
    "autofile.plugins.templates.uti",
    "autofile.plugins.templates.finder",
    "autofile.plugins.templates.mdls",
    "autofile.plugins.templates.format",
    "autofile.plugins.templates.filepath",
    "autofile.plugins.templates.filedates",
    "autofile.plugins.templates.filestat",
)


def get_plugin_manager():
    pm = pluggy.PluginManager(APP_NAME)
    pm.add_hookspecs(hookspecs)
    pm.load_setuptools_entrypoints(APP_NAME)
    # pm.register(lib)
    return pm


PM = get_plugin_manager()

# Load default plugins
for plugin in DEFAULT_PLUGINS:
    mod = importlib.import_module(plugin)
    PM.register(mod, plugin)

# help_text = PM.hook.get_template_help()

# from .utils import expand_and_validate_filepath, load_function

# ensure locale set to user's locale
locale.setlocale(locale.LC_ALL, "")

OTL_GRAMMAR_MODEL = str(pathlib.Path(__file__).parent / "template.tx")
"""TextX metamodel for template language """

# # Permitted multi-value substitutions (each of these returns None or 1 or more values)
# TEMPLATE_SUBSTITUTIONS_MULTI_VALUED = {
#     # "{shell_quote}": "Use in form '{shell_quote,TEMPLATE}'; quotes the rendered TEMPLATE value(s) for safe usage in the shell, e.g. My file.jpeg => 'My file.jpeg'; only adds quotes if needed.",
#     # "{function}": "Execute a python function from an external file and use return value as template substitution. "
#     # + "Use in format: {function:file.py::function_name} where 'file.py' is the name of the python file and 'function_name' is the name of the function to call. "
#     # + "The function will be passed the PhotoInfo object for the photo. "
#     # + "See https://github.com/RhetTbull/osxphotos/blob/master/examples/template_function.py for an example of how to implement a template function.",
# }


FILTER_VALUES = {
    "lower": "Convert value to lower case, e.g. 'Value' => 'value'.",
    "upper": "Convert value to upper case, e.g. 'Value' => 'VALUE'.",
    "strip": "Strip whitespace from beginning/end of value, e.g. ' Value ' => 'Value'.",
    "titlecase": "Convert value to title case, e.g. 'my value' => 'My Value'.",
    "capitalize": "Capitalize first word of value and convert other words to lower case, e.g. 'MY VALUE' => 'My value'.",
    "braces": "Enclose value in curly braces, e.g. 'value => '{value}'.",
    "parens": "Enclose value in parentheses, e.g. 'value' => '(value')",
    "brackets": "Enclose value in brackets, e.g. 'value' => '[value]'",
    "shell_quote": "Quotes the value for safe usage in the shell, e.g. My file.jpeg => 'My file.jpeg'; only adds quotes if needed.",
    # "function": "Run custom python function to filter value; use in format 'function:/path/to/file.py::function_name'. See example at https://github.com/RhetTbull/osxphotos/blob/master/examples/template_filter.py",
}

# PATH_SEP_DEFAULT = os.path.sep


class FileTemplateParser:
    """Parser for FileTemplate"""

    # implemented as Singleton

    def __new__(cls, *args, **kwargs):
        """create new object or return instance of already created singleton"""
        if not hasattr(cls, "instance") or not cls.instance:
            cls.instance = super().__new__(cls)

        return cls.instance

    def __init__(self):
        """return existing singleton or create a new one"""

        if hasattr(self, "metamodel"):
            return

        self.metamodel = metamodel_from_file(OTL_GRAMMAR_MODEL, skipws=False)

    def parse(self, template_statement):
        """Parse a template_statement string"""
        return self.metamodel.model_from_str(template_statement)

    def fields(self, template_statement):
        """Return list of fields found in a template statement; does not verify that fields are valid"""
        model = self.parse(template_statement)
        return [ts.template.field for ts in model.template_strings if ts.template]


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

        # get parser singleton
        self.parser = FileTemplateParser()

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
        # self.exiftool = options.exiftool or ExifToolCaching(
        #     self.filepath, exiftool=self.exiftool_path
        # )

    def render(
        self,
        template: str,
        options: RenderOptions,
    ):
        """Render a filename or directory template

        Args:
            template: str template
            options: a RenderOptions instance

        Returns:
            ([rendered_strings], [unmatched]): tuple of list of rendered strings and list of unmatched template values
        """

        if type(template) is not str:
            raise TypeError(f"template must be type str, not {type(template)}")

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

        try:
            model = self.parser.parse(template)
        except TextXSyntaxError as e:
            raise SyntaxError(e)

        if not model:
            # empty string
            return [], []

        return self._render_statement(model)

    def _render_statement(
        self,
        statement,
    ):
        results = []
        unmatched = []
        for ts in statement.template_strings:
            results, unmatched = self._render_template_string(
                ts,
                results=results,
                unmatched=unmatched,
            )

        rendered_strings = results

        if self.filename:
            rendered_strings = [
                sanitize_filename(rendered_str) for rendered_str in rendered_strings
            ]

        if self.strip:
            rendered_strings = [
                rendered_str.strip() for rendered_str in rendered_strings
            ]

        return rendered_strings, unmatched

    def _render_template_string(
        self,
        ts,
        results=None,
        unmatched=None,
    ):
        """Render a TemplateString object"""

        results = results or [""]
        unmatched = unmatched or []

        if ts.template:
            # have a template field to process
            field = ts.template.field
            subfield = ts.template.subfield

            # process filters
            filters = []
            if ts.template.filter is not None:
                filters = ts.template.filter.value

            # process delim
            if ts.template.delim is not None:
                # if value is None, means format was {+field}
                delim = ts.template.delim.value or ""
            else:
                delim = None

            if ts.template.bool is not None:
                is_bool = True
                if ts.template.bool.value is not None:
                    bool_val, u = self._render_statement(
                        ts.template.bool.value,
                    )
                    unmatched.extend(u)
                else:
                    # blank bool value
                    bool_val = [""]
            else:
                is_bool = False
                bool_val = None

            # process default
            if ts.template.default is not None:
                # default is also a TemplateString
                if ts.template.default.value is not None:
                    default, u = self._render_statement(
                        ts.template.default.value,
                    )
                    unmatched.extend(u)
                else:
                    # blank default value
                    default = [""]
            else:
                default = []

            # process conditional
            if ts.template.conditional is not None:
                operator = ts.template.conditional.operator
                negation = ts.template.conditional.negation
                if ts.template.conditional.value is not None:
                    # conditional value is also a TemplateString
                    conditional_value, u = self._render_statement(
                        ts.template.conditional.value,
                        # path_sep=path_sep,
                    )
                    unmatched.extend(u)
                else:
                    # this shouldn't happen
                    conditional_value = [""]
            else:
                operator = None
                negation = None
                conditional_value = []

            # vals = []
            # # elif field == "function":
            # #     if subfield is None:
            # #         raise ValueError(
            # #             "SyntaxError: filename and function must not be null with {function::filename.py:function_name}"
            # #         )
            # #     vals = self.get_template_value_function(
            # #         subfield,
            # #     )

            # pass processing to plugins to get values
            vals = self.hook.get_template_value(
                filepath=self.filepath,
                field=field,
                subfield=subfield,
                default=default,
                options=self.options,
            )

            if vals:
                if self.filename:
                    vals = [sanitize_pathpart(v) for v in vals]
                elif self.dirname:
                    vals = [sanitize_dirname(v) for v in vals]

            if vals is None:
                raise UnknownFieldError(f"Unknown template field: {field}")

            vals = [val for val in vals if val is not None]

            if self.expand_inplace or delim is not None:
                sep = delim if delim is not None else self.inplace_sep
                vals = [sep.join(sorted(vals))] if vals else []

            for filter_ in filters:
                vals = self.get_template_value_filter(filter_, vals)

            # process find/replace
            if ts.template.findreplace:
                new_vals = []
                for val in vals:
                    for pair in ts.template.findreplace.pairs:
                        find = pair.find or ""
                        repl = pair.replace or ""
                        val = val.replace(find, repl)
                    new_vals.append(val)
                vals = new_vals

            if operator:
                # have a conditional operator

                def string_test(test_function):
                    """Perform string comparison using test_function; closure to capture conditional_value, vals, negation"""
                    match = False
                    for c in conditional_value:
                        for v in vals:
                            if test_function(v, c):
                                match = True
                                break
                        if match:
                            break
                    if (match and not negation) or (negation and not match):
                        return ["True"]
                    else:
                        return []

                def comparison_test(test_function):
                    """Perform numerical comparisons using test_function; closure to capture conditional_val, vals, negation"""
                    if len(vals) != 1 or len(conditional_value) != 1:
                        raise ValueError(
                            f"comparison operators may only be used with a single value: {vals} {conditional_value}"
                        )
                    try:
                        match = bool(
                            test_function(float(vals[0]), float(conditional_value[0]))
                        )
                        if (match and not negation) or (negation and not match):
                            return ["True"]
                        else:
                            return []
                    except ValueError as e:
                        raise ValueError(
                            f"comparison operators may only be used with values that can be converted to numbers: {vals} {conditional_value}"
                        )

                if operator in ["contains", "matches", "startswith", "endswith"]:
                    # process any "or" values separated by "|"
                    temp_values = []
                    for c in conditional_value:
                        temp_values.extend(c.split("|"))
                    conditional_value = temp_values

                if operator == "contains":
                    vals = string_test(lambda v, c: c in v)
                elif operator == "matches":
                    vals = string_test(lambda v, c: v == c)
                elif operator == "startswith":
                    vals = string_test(lambda v, c: v.startswith(c))
                elif operator == "endswith":
                    vals = string_test(lambda v, c: v.endswith(c))
                elif operator == "==":
                    match = sorted(vals) == sorted(conditional_value)
                    if (match and not negation) or (negation and not match):
                        vals = ["True"]
                    else:
                        vals = []
                elif operator == "!=":
                    match = sorted(vals) != sorted(conditional_value)
                    if (match and not negation) or (negation and not match):
                        vals = ["True"]
                    else:
                        vals = []
                elif operator == "<":
                    vals = comparison_test(lambda v, c: v < c)
                elif operator == "<=":
                    vals = comparison_test(lambda v, c: v <= c)
                elif operator == ">":
                    vals = comparison_test(lambda v, c: v > c)
                elif operator == ">=":
                    vals = comparison_test(lambda v, c: v >= c)

            if is_bool:
                vals = default if not vals else bool_val
            elif not vals:
                vals = default or [self.none_str]

            pre = ts.pre or ""
            post = ts.post or ""

            rendered = [pre + val + post for val in vals]
            results_new = []
            for ren in rendered:
                for res in results:
                    res_new = res + ren
                    results_new.append(res_new)
            results = results_new

        else:
            # no template
            pre = ts.pre or ""
            post = ts.post or ""
            results = [r + pre + post for r in results]

        return results, unmatched

    def get_template_value_filter(self, filter_, values):
        if filter_ == "lower":
            if values and type(values) == list:
                value = [v.lower() for v in values]
            else:
                value = [values.lower()] if values else []
        elif filter_ == "upper":
            if values and type(values) == list:
                value = [v.upper() for v in values]
            else:
                value = [values.upper()] if values else []
        elif filter_ == "strip":
            if values and type(values) == list:
                value = [v.strip() for v in values]
            else:
                value = [values.strip()] if values else []
        elif filter_ == "capitalize":
            if values and type(values) == list:
                value = [v.capitalize() for v in values]
            else:
                value = [values.capitalize()] if values else []
        elif filter_ == "titlecase":
            if values and type(values) == list:
                value = [v.title() for v in values]
            else:
                value = [values.title()] if values else []
        elif filter_ == "braces":
            if values and type(values) == list:
                value = ["{" + v + "}" for v in values]
            else:
                value = ["{" + values + "}"] if values else []
        elif filter_ == "parens":
            if values and type(values) == list:
                value = ["(" + v + ")" for v in values]
            else:
                value = ["(" + values + ")"] if values else []
        elif filter_ == "brackets":
            if values and type(values) == list:
                value = ["[" + v + "]" for v in values]
            else:
                value = ["[" + values + "]"] if values else []
        elif filter_ == "shell_quote":
            if values and type(values) == list:
                value = [shlex.quote(v) for v in values]
            else:
                value = [shlex.quote(values)] if values else []
        # elif filter_.startswith("function:"):
        # value = self.get_template_value_filter_function(filter_, values)
        else:
            raise ValueError(f"Unhandled filter: {filter_}")
        return value


def get_template_help() -> List[Union[str, List]]:
    """Return help for template system as list of markdown strings or lists of lists"""
    # TODO: would be better to use importlib.abc.ResourceReader but I can't find a single example of how to do this
    help_file = pathlib.Path(__file__).parent / "template.md"
    with open(help_file, "r") as fd:
        md = [fd.read()]

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


# def lol_to_md_table(lol: List[List]) -> str:
#     """Convert a dict to a markdown table; assumes each list is the same length"""
#     if not lol:
#         return ""
#
#     markdowntable = ""
#     # Make a string of all the keys in the first dict with pipes before after and between each key
#     markdownheader = "| " + " | ".join(map(str, lol[0])) + " |"
#     # Make a header separator line with dashes instead of key names
#     markdownheaderseparator = "|-----" * len(lol[0]) + "|"
#     # Add the header row and separator to the table
#     markdowntable += markdownheader + "\n"
#     markdowntable += markdownheaderseparator + "\n"
#     # Loop through the list of lists outputting the rows
#     for row in lol[1:]:
#         markdownrow = "".join("| " + str(col) + " " for col in row)
#         markdowntable += markdownrow + "|" + "\n"
#     print(f"{markdowntable=}")
#     return markdowntable
#
# def get_template_value_function(
#     self,
#     subfield,
# ):
#     """Get template value from external function"""

#     if "::" not in subfield:
#         raise ValueError(
#             f"SyntaxError: could not parse function name from '{subfield}'"
#         )

#     filename, funcname = subfield.split("::")

#     filename_validated = expand_and_validate_filepath(filename)
#     if not filename_validated:
#         raise ValueError(f"'{filename}' does not appear to be a file")

#     template_func = load_function(filename_validated, funcname)
#     values = template_func(self.photo, options=self.options)

#     if not isinstance(values, (str, list)):
#         raise TypeError(
#             f"Invalid return type for function {funcname}: expected str or list"
#         )
#     if type(values) == str:
#         values = [values]

#     # sanitize directory names if needed
#     if self.filename:
#         values = [sanitize_pathpart(value) for value in values]
#     elif self.dirname:
#         # sanitize but don't replace any "/" as user function may want to create sub directories
#         values = [sanitize_dirname(value, replacement=None) for value in values]

#     return values

# def get_template_value_filter_function(self, filter_, values):
#     """Filter template value from external function"""

#     filter_ = filter_.replace("function:", "")

#     if "::" not in filter_:
#         raise ValueError(
#             f"SyntaxError: could not parse function name from '{filter_}'"
#         )

#     filename, funcname = filter_.split("::")

#     filename_validated = expand_and_validate_filepath(filename)
#     if not filename_validated:
#         raise ValueError(f"'{filename}' does not appear to be a file")

#     template_func = load_function(filename_validated, funcname)

#     if not isinstance(values, (list, tuple)):
#         values = [values]
#     values = template_func(values)

#     if not isinstance(values, list):
#         raise TypeError(
#             f"Invalid return type for function {funcname}: expected list"
#         )

#     return values
