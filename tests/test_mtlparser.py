"""Test for MTLParser"""

import locale
import os

import pytest

from autofile.mtlparser import SyntaxError, MTLParser

PUNCTUATION = {
    "comma": ",",
    "semicolon": ";",
    "pipe": "|",
    "percent": "%",
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

FIELD_VALUES = {
    "foo": ["Foo", "Bar"],
    "foo:foo": ["Foo"],
    "foo:bar": ["Bar"],
    "bar": ["Foo Bar"],
    "baz": [None],
    "fizz": [" fizz buzz "],
    "foobar": ["foo,bar"],
    "answer": ["42"],
    "list": ["a", "c", "b", "b", "c", "c"],
}

TEST_DATA = [
    # basic templates
    ["{foo}", ["Foo", "Bar"]],
    ["{+foo}", ["BarFoo"]],
    ["{, +foo}", ["Bar, Foo"]],
    ["{foo:foo}", ["Foo"]],
    ["{foo:bar}", ["Bar"]],
    ["{bar}", ["Foo Bar"]],
    ["{baz}", ["_"]],
    ["{baz,BAZ}", ["BAZ"]],
    ["{baz,{foo:bar}}", ["Bar"]],
    ["{fizz}", [" fizz buzz "]],
    ["{fizz[z,s]}", [" fiss buss "]],
    ["{fizz[z,s|i,u]}", [" fuss buss "]],
    # filters
    ["{+foo|lower}", ["barfoo"]],
    ["{+foo|upper}", ["BARFOO"]],
    ["{fizz|strip}", ["fizz buzz"]],
    ["{fizz|strip|capitalize}", ["Fizz buzz"]],
    ["{fizz|titlecase}", [" Fizz Buzz "]],
    ["{foo:foo|braces}", ["{Foo}"]],
    ["{foo:foo|parens}", ["(Foo)"]],
    ["{foo|brackets}", ["[Foo]", "[Bar]"]],
    ["{fizz|shell_quote}", ["' fizz buzz '"]],
    ["{fizz|strip|split( )}", ["fizz", "buzz"]],
    ["{foobar|split(,)}", ["foo", "bar"]],
    ["{foobar|autosplit}", ["foo", "bar"]],
    ["{fizz|autosplit}", ["fizz", "buzz"]],
    ["{foobar|chop(2)}", ["foo,b"]],
    ["{foobar|chomp(2)}", ["o,bar"]],
    ["{list|sort}", ["a", "b", "b", "c", "c", "c"]],
    ["{list|rsort}", ["c", "c", "c", "b", "b", "a"]],
    ["{list|uniq|sort}", ["a", "b", "c"]],
    ["{list|uniq|sort|reverse}", ["c", "b", "a"]],
    ["{list|uniq|sort|reverse|join(:)}", ["c:b:a"]],
    ["{var:myvar,{percent}}{list|uniq|sort|reverse|join(%myvar)}", ["c%b%a"]],
    ["{list|uniq|sort|append(d)}", ["a", "b", "c", "d"]],
    ["{list|uniq|sort|prepend(d)}", ["d", "a", "b", "c"]],
    ["{list|uniq|sort|remove(b)}", ["a", "c"]],
    ["{foo contains Foo?{foo|remove(Foo)},{foo}}", ["Bar"]],
    # format
    ["{strip,{fizz}}", ["fizz buzz"]],
    ["{format:int:03d,{answer}}", ["042"]],
    ["{format:float:10.4f,{answer}}", ["   42.0000"]],
    ["{format:str:-^10,{answer}}", ["----42----"]],
    # variables
    ["{var:myvar,{semicolon}}{foo:foo}{%myvar}", ["Foo;"]],
    ["{var:myvar,{semicolon}}{;+foo[%myvar,%%]}", ["Bar%Foo"]],
    ["{var:myvar,{semicolon}}{;+foo|split(%myvar)}", ["Bar", "Foo"]],
    ["{var:myvar,X}{X+foo|split(%myvar)}", ["Bar", "Foo"]],
    ["{var:myvar,{percent}}{%myvar+foo}", ["Bar%Foo"]],
    # conditionals
    ["{foo contains Foo?YES,NO}", ["YES"]],
    ["{foo contains Fo?YES,NO}", ["YES"]],
    ["{foo:foo contains Foo?YES,NO}", ["YES"]],
    ["{foo not contains Foo?YES,NO}", ["NO"]],
    ["{foo contains FOO?YES,NO}", ["NO"]],
    ["{foo not contains FOO?YES,NO}", ["YES"]],
    ["{foo matches Foo?YES,NO}", ["YES"]],
    ["{foo matches Fo?YES,NO}", ["NO"]],
    ["{fizz|strip startswith fizz?YES,NO}", ["YES"]],
    ["{fizz|strip startswith buzz?YES,NO}", ["NO"]],
    ["{fizz|strip not startswith buzz?YES,NO}", ["YES"]],
    ["{fizz|strip endswith buzz?YES,NO}", ["YES"]],
    ["{fizz|strip endswith fizz?YES,NO}", ["NO"]],
    ["{fizz|strip not endswith buzz?YES,NO}", ["NO"]],
    ["{fizz|strip == fizz buzz?YES,NO}", ["YES"]],
    ["{fizz|strip != fizz buzz?YES,NO}", ["NO"]],
    ["{answer == 42?YES,NO}", ["YES"]],
    ["{answer == 41?YES,NO}", ["NO"]],
    ["{answer != 42?YES,NO}", ["NO"]],
    ["{answer != 41?YES,NO}", ["YES"]],
    ["{answer <= 42?YES,NO}", ["YES"]],
    ["{answer >= 42?YES,NO}", ["YES"]],
    ["{answer <= 40?YES,NO}", ["NO"]],
    ["{answer <= 43?YES,NO}", ["YES"]],
    ["{answer >= 40?YES,NO}", ["YES"]],
    ["{answer >= 43?YES,NO}", ["NO"]],
    ["{answer > 43?YES,NO}", ["NO"]],
    ["{answer < 43?YES,NO}", ["YES"]],
]


class CustomParser:
    def __init__(
        self,
        sanitize=None,
        sanitize_value=None,
        expand_inplace=False,
        inplace_sep=",",
        none_str="_",
    ):
        self.parser = MTLParser(
            get_field_values=self.get_field_values,
            sanitize=sanitize,
            sanitize_value=sanitize_value,
            expand_inplace=expand_inplace,
            inplace_sep=inplace_sep,
            none_str=none_str,
        )

    def get_field_values(self, field, subfield, default):
        if subfield:
            return FIELD_VALUES.get(f"{field}:{subfield}")
        else:
            return FIELD_VALUES.get(f"{field}")

    def render(self, template_string):
        return self.parser.render(template_string)


@pytest.fixture
def setlocale():
    # set locale and timezone for testing
    locale.setlocale(locale.LC_ALL, "en_US")
    tz = os.environ.get("TZ")
    os.environ["TZ"] = "US/Pacific"
    yield
    if tz:
        os.environ["TZ"] = tz


def test_template_render_punctuation():
    """Test that punctuation is rendered correctly"""
    for key, value in PUNCTUATION.items():
        assert CustomParser().render("{" + key + "}") == [value]


@pytest.mark.parametrize("data", TEST_DATA)
def test_template_render(data, setlocale):
    """Test template rendering"""
    template = CustomParser()
    result = template.render(data[0])
    assert result == data[1]


def test_expand_inplace():
    """Test expand_inplace"""
    template = CustomParser(expand_inplace=True)
    result = template.render("{foo}")
    assert result[0] == "Bar,Foo"  # expand_inplace sorts the values

    template = CustomParser(expand_inplace=True, inplace_sep="/")
    result = template.render("{foo}")
    assert result[0] == "Bar/Foo"


def test_template_var_error():
    """Test template var error"""
    template = CustomParser()
    with pytest.raises(SyntaxError):
        template.render("{var:foo}")
    with pytest.raises(SyntaxError):
        template.render("{%bar}")


def test_sanitize():
    """Test sanitize function"""
    template = CustomParser(sanitize=lambda x: x.upper())
    result = template.render("foo {foo:bar}")
    assert result == ["FOO BAR"]


def test_sanitize_value():
    """Test sanitize_value function"""

    def sanitize_value(value):
        return value.lower()

    template = CustomParser(sanitize_value=sanitize_value)
    result = template.render("{foo}")
    assert result == ["foo", "bar"]


def test_sanitize_value_2():
    """Test sanitize_value function"""

    def sanitize_value(value):
        return value.lower()

    template = CustomParser(sanitize_value=sanitize_value)
    result = template.render("Foo {foo:bar}")
    assert result == ["Foo bar"]
