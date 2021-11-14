""" Metadata Template Language (MTL) parser """

# This parser forms the basis for the template system used by osxphotos, exif2findertags, and autofile

# ZZZ add way to get help for built-ins, add mtlparser.md

import pathlib
import re
import shlex
from textwrap import dedent
from typing import Callable, Dict, List, Optional, Union

from textx import TextXSyntaxError, metamodel_from_file


class UnknownFieldError(Exception):
    """Raised when a field is not known"""

    pass


class SyntaxError(Exception):
    """Raised when template engine cannot parse the template string"""

    pass


MTL_GRAMMAR_MODEL = str(pathlib.Path(__file__).parent / "mtlparser.tx")
"""TextX metamodel for template language """


PUNCTUATION_FIELDS = {
    "{comma}": ["A comma: ','", ","],
    "{semicolon}": ["A semicolon: ';'", ";"],
    "{questionmark}": ["A question mark: '?'", "?"],
    "{pipe}": ["A vertical pipe: '|'", "|"],
    "{percent}": ["A percent sign: '%'", "%"],
    "{openbrace}": ["An open brace: '{'", "{"],
    "{closebrace}": ["A close brace: '}'", "}"],
    "{openparens}": ["An open parentheses: '('", "("],
    "{closeparens}": ["A close parentheses: ')'", ")"],
    "{openbracket}": ["An open bracket: '['", "["],
    "{closebracket}": ["A close bracket: ']'", "]"],
    "{newline}": [r"A newline: '\n'", "\n"],
    "{lf}": [r"A line feed: '\n', alias for {newline}", "\n"],
    "{cr}": [r"A carriage return: '\r'", "\r"],
    "{crlf}": [r"a carriage return + line feed: '\r\n'", "\r\n"],
}
"""The built-in punctuation fields"""

FORMAT_FIELDS = {
    "{strip}": [
        "Use in form '{strip,TEMPLATE}'; strips whitespace from begining and end of rendered TEMPLATE value(s)."
    ],
    "{format}": [
        "Use in form, '{format:TYPE:FORMAT,TEMPLATE}'; converts TEMPLATE value to TYPE then formats the value using python string formatting codes specified by FORMAT; TYPE is one of: 'int', 'float', or 'str'."
    ],
}


def format_str_value(value, format_str):
    """Format value based on format code in field in format id:02d"""
    if not format_str:
        return str(value)
    format_str = "{0:" + f"{format_str}" + "}"
    return format_str.format(value)


class MTLParserModel:
    """Parser model for MTLParser"""

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

        self.metamodel = metamodel_from_file(MTL_GRAMMAR_MODEL, skipws=False)

    def parse(self, template_statement):
        """Parse a template_statement string"""
        return self.metamodel.model_from_str(template_statement)

    def fields(self, template_statement):
        """Return list of fields found in a template statement; does not verify that fields are valid"""
        model = self.parse(template_statement)
        return [ts.template.field for ts in model.template_strings if ts.template]


class MTLParser:
    """Parser class to render a template string written in Metadata Template Language (MTL)"""

    def __init__(
        self,
        get_field_values: Callable,
        sanitize: Optional[Callable] = None,
        sanitize_value: Optional[Callable] = None,
        expand_inplace: bool = False,
        inplace_sep: str = ",",
        none_str: str = "_",
    ):
        """Inits the MTLParser class

        Args:
            get_field_values: function to get the values for a template; has signature
                get_field_values(filepath: str, field: str, subfield: str, default: List[str]) -> Optional[List[Optional[str]]]
            sanitize: optional function to sanitize the rendered string (for example, to validate the string conforms to a valid filename); has signature:
                sanitize(value: str) -> str
            sanitize_value: optional function to sanitize the value of a field; has signature:
                sanitize_value(value: str) -> str
            expand_inplace: if True, expand multi-value fields in place, rather than returning a list of values
            inplace_sep: separator to use when expanding multi-value fields in place
            none_str: string to use when a field value is None (the default value if a default isn't provided in the template string)
        """

        # get parser singleton
        self.parser = MTLParserModel()

        # list of methods to call (in order) to get the values for a field
        self.field_values = [
            get_field_values,
            self.get_punctuation_values,
            self.get_format_values,
        ]

        self.sanitize = sanitize
        self.sanitize_value = sanitize_value
        self.expand_inplace = expand_inplace
        self.inplace_sep = inplace_sep
        self.none_str = none_str
        self.variables = {}

    def render(
        self,
        template: str,
    ):
        """Render an MTL template string

        Args:
            template: str template

        Returns:
            [rendered_strings]: list of rendered strings
        """

        if type(template) is not str:
            raise TypeError(f"template must be type str, not {type(template)}")

        self.variables = {}

        try:
            model = self.parser.parse(template)
        except TextXSyntaxError as e:
            raise SyntaxError(e)

        if not model:
            # empty string
            return []

        return self._render_statement(model)

    def _render_statement(
        self,
        statement,
    ):
        results = []
        for ts in statement.template_strings:
            results = self._render_template_string(
                ts,
                results=results,
            )

        rendered_strings = results

        if self.sanitize:
            rendered_strings = [self.sanitize(v) for v in rendered_strings]

        return rendered_strings

    def _render_template_string(
        self,
        ts,
        results=None,
    ):
        """Render a TemplateString object"""

        results = results or [""]

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
                delim = self.expand_variables(delim)
                if len(delim) != 1:
                    raise SyntaxError(f"delim must have a single value: {delim}")
                delim = delim[0]
            else:
                delim = None

            if ts.template.bool is not None:
                is_bool = True
                if ts.template.bool.value is not None:
                    bool_val = self._render_statement(
                        ts.template.bool.value,
                    )
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
                    default = self._render_statement(
                        ts.template.default.value,
                    )
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
                    conditional_value = self._render_statement(
                        ts.template.conditional.value,
                        # path_sep=path_sep,
                    )
                else:
                    # this shouldn't happen
                    conditional_value = [""]
            else:
                operator = None
                negation = None
                conditional_value = []

            if field.startswith("%"):
                # variable in form {%var}
                vals = self.variables.get(field[1:], None)
                if vals is None:
                    raise SyntaxError(f"Variable '{field[1:]}' is not defined.")
            elif field == "var":
                if not subfield or not default:
                    raise SyntaxError(
                        "var must have a subfield and value in form {var:subfield,value}"
                    )
                self.variables[subfield] = default
                vals = []
            else:
                vals = self.get_field_values(field, subfield, default)

            if vals and self.sanitize_value:
                vals = [self.sanitize_value(v) for v in vals]

            if vals is None:
                if field:
                    raise UnknownFieldError(f"Unknown template field: {field}")
                vals = []

            vals = [val for val in vals if val is not None]

            if self.expand_inplace or delim is not None:
                sep = delim if delim is not None else self.inplace_sep
                vals = [sep.join(sorted(vals))] if vals else []

            for filter_ in filters:
                vals = self.get_filter_values(filter_, vals)

            # process find/replace
            if ts.template.findreplace:
                new_vals = []
                for val in vals:
                    for pair in ts.template.findreplace.pairs:
                        find = pair.find or ""
                        find_vars = self.expand_variables(find)
                        if len(find_vars) != 1:
                            raise SyntaxError(
                                f"find/replace must have a single value to find or replace: {find_vars}"
                            )
                        find = find_vars[0]

                        repl = pair.replace or ""
                        repl_vars = self.expand_variables(repl)
                        if len(repl_vars) != 1:
                            raise SyntaxError(
                                f"find/replace must have a single value to replace: {repl_vars}"
                            )
                        repl = repl_vars[0]
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
                    # returns True if any of the values match the condition
                    if len(conditional_value) != 1:
                        raise SyntaxError(
                            f"comparison operators may only be used with a single conditional value: {conditional_value}"
                        )
                    try:
                        match = any(
                            bool(test_function(float(v), float(conditional_value[0])))
                            for v in vals
                        )
                        if (match and not negation) or (negation and not match):
                            return ["True"]
                        else:
                            return []
                    except ValueError as e:
                        raise SyntaxError(
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
            elif not vals and field != "var":
                # don't assign default value if the template was variable assignment
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

        return results

    def expand_variables(self, value: str) -> List[str]:
        """Expand variables in value"""
        # replace any variables with their values
        values = [value]
        new_values = []
        # allow %% to escape %, match variables in form %var
        variable_match = re.compile(r"(?:%%)*(%[\w]+)?")
        while True:
            for value in values:
                match = variable_match.search(value)
                if not match or not match.group(1):
                    break
                var = match.group(1)
                var_name = var[1:]
                if var_name not in self.variables:
                    raise SyntaxError(f"Variable '{var_name}' is not defined.")
                for val in values:
                    for var_val in self.variables[var_name]:
                        new_values.append(
                            re.sub(r"(%%)*" + f"{var}", r"\g<1>" + var_val, val)
                        )
            if new_values == values or not new_values:
                break
            values = new_values.copy()
            new_values = []

        # replace %% with %
        # any %% left in the string will be replaced with %
        values = [value.replace("%%", "%") for value in values]

        return values

    def get_field_values(
        self, field: str, subfield: str, default: List[str]
    ) -> Optional[List[Optional[str]]]:
        """Return values for a given template field"""

        for get_function in self.field_values:
            values = get_function(field, subfield, default)
            if values is not None:
                return values
        return None

    def get_punctuation_values(
        self, field: str, subfield: str, default: List[str]
    ) -> Optional[List[Optional[str]]]:
        """Return values for punctuation template fields, e.g. {crlf}, etc."""
        value = PUNCTUATION_FIELDS.get("{" + field + "}")
        return [value[1]] if value else None

    def get_format_values(
        self, field: str, subfield: str, default: List[str]
    ) -> Optional[List[Optional[str]]]:
        """Return values for {strip}, {format} templates"""
        if field == "strip":
            return [v.strip() for v in default]

        if field == "format":
            if not subfield or ":" not in subfield:
                raise ValueError("{format} requires subfield in form TYPE:FORMAT")
            type_, format_str = subfield.split(":", 1)
            if type_ not in ("int", "float", "str"):
                raise ValueError(
                    f"'{type_}' is not a valid type for {format}: must be one of 'int', 'float', 'str'"
                )
            if type_ == "int":
                default = [int(v) for v in default]
            elif type_ == "float":
                default = [float(v) for v in default]
            format_str = self.expand_variables(format_str)
            if len(format_str) != 1:
                raise ValueError(
                    f"{format} format string must be a single value, not {format_str}"
                )
            format_str = format_str[0]
            return [format_str_value(v, format_str) for v in default]

        return None

    def get_filter_values(self, filter_, values):
        """Return filtered values"""
        if re.search(r"\(.*\)", filter_):
            # filter has arguments
            filter_, args = filter_.split("(", 1)
            args = args.rstrip(")")
            args = self.expand_variables(args)
            if len(args) != 1:
                raise SyntaxError(f"Filter arguments must be a single value: {args}")
            args = args[0]
        else:
            args = None
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
        elif filter_ == "split":
            # split on delimiter
            delim = args
            if delim:
                new_values = []
                for v in values:
                    new_values.extend(v.split(delim))
                value = new_values
            else:
                value = values
        elif filter_ == "chop":
            # chop off characters from the end
            chop = args
            try:
                chop = int(chop)
            except ValueError:
                raise SyntaxError(f"Invalid value for chop: {chop}")
            value = [v[:-chop] for v in values] if chop else values
        elif filter_ == "chomp":
            # chop off characters from the beginning
            chomp = args
            try:
                chomp = int(chomp)
            except ValueError:
                raise SyntaxError(f"Invalid value for chomp: {chomp}")
            value = [v[chomp:] for v in values] if chomp else values
        elif filter_ == "autosplit":
            # try to split keyword strings automatically
            temp_values = [v.replace(",", " ") for v in values]
            temp_values = [v.replace(";", " ") for v in temp_values]
            value = []
            for val in temp_values:
                value.extend(val.split())
        elif filter_ == "sort":
            # sort list of values
            value = sorted(values)
        elif filter_ == "rsort":
            # reverse sort list of values
            value = sorted(values, reverse=True)
        elif filter_ == "reverse":
            # reverse list of values
            value = values[::-1]
        elif filter_ == "uniq":
            # remove duplicate values from list
            temp_values =[]
            [temp_values.append(v) for v in values if v not in temp_values]
            value = temp_values
        elif filter_ == "join":
            # join list of values with delimiter
            delim = args
            value = [delim.join(values)]
        elif filter_ == "append":
            # append value to list
            value = values + [args]
        elif filter_ == "prepend":
            # prepend value to list
            value = [args] + values
        elif filter_ == "remove":
            # remove value from list
            value = [v for v in values if v != args]
        # elif filter_.startswith("function:"):
        # value = self.get_template_value_filter_function(filter_, values)
        else:
            raise SyntaxError(f"Unhandled filter: {filter_}")
        return value
