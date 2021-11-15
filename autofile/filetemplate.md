autofile contains a rich templating system which allows fine-grained control over the output format of metadata. The templating system converts one or template statements, written in metadata templating language (MTL), to one or more rendered values using metadata information from the file being processed.

In its simplest form, a template statement has the form: `"{template_field}"`, for example `"{size}"` which resolves to the size of the file. Template fields may also have subfields delineated by a `:` as in `"{audio:artist}"` which resolves to the artist name for an audio file (e.g. mp3).  In this example, the field is `audio` and the subfield is `artist`.  Template fields may also have attributes delineated by a `.` as in `"{created.year}"` which resolves to the 4-digit year of the file creation date. In this example, the field is `created` and the attribute is `year`.

Template statements may contain one or more modifiers.  The full syntax is:

`"pretext{delim+template_field:subfield|filter[find,replace] conditional?bool_value,default}posttext"`

Template statements are white-space sensitive meaning that white space (spaces, tabs) changes the meaning of the template statement.

`pretext` and `posttext` are free form text.  For example, if an image file has Title (e.g. XMP:Title) "My file Title". the template statement `"The title of the file is {exiftool:Title}"`, resolves to `"The title of the file is My file Title"`.  The `pretext` in this example is `"The title if the file is "` and the template_field is `{Title}`.  Note: some punctuation such as commas cannot be used in the pretext or posttext.  For this reason, the template system provides special punctuation templates like `{comma}` to insert punctuation where needed. For example: `{exiftool:Make}{comma}{exiftool:Model}` could resolve to `Apple,iPhone SE`. 

**Delimiter**

`delim`: optional delimiter string to use when expanding multi-valued template values in-place

`+`: If present before template `name`, expands the template in place.  If `delim` not provided, values are joined with no delimiter.

e.g. if image file keywords are `["foo","bar"]`:

- `"{exiftool:Keywords}"` renders to `"foo", "bar"`
- `"{,+exiftool:Keywords}"` renders to: `"foo,bar"`
- `"{; +exiftool:Keywords}"` renders to: `"foo; bar"`
- `"{+exiftool:Keywords}"` renders to `"foobar"`

`template_field`: The template field to resolve.  

`:subfield`: Templates may have sub-fields; reserved for future use.

**Filters**

`|filter`: You may optionally append one or more filter commands to the end of the template field using the vertical pipe ('|') symbol.  Filters may be combined, separated by '|' as in: `{user|capitalize|parens}`.

Valid filters are:

- lower: Convert value to lower case, e.g. 'Value' => 'value'.
- upper: Convert value to upper case, e.g. 'Value' => 'VALUE'.
- strip: Strip whitespace from beginning/end of value, e.g. ' Value ' => 'Value'.
- titlecase: Convert value to title case, e.g. 'my value' => 'My Value'.
- capitalize: Capitalize first word of value and convert other words to lower case, e.g. 'MY VALUE' => 'My value'.
- braces: Enclose value in curly braces, e.g. 'value => '{value}'.
- parens: Enclose value in parentheses, e.g. 'value' => '(value').
- brackets: Enclose value in brackets, e.g. 'value' => '[value]'.
- split(x): Split value into a list of values using x as delimiter, e.g. 'value1;value2' => ['value1', 'value2'] if used with split(;).
- autosplit: Automatically split delimited string into separate values (for example, keyword string in docx files); will split strings delimited by comma, semicolon, or space, e.g. 'value1,value2' => ['value1', 'value2'].
- chop(x): Remove x characters off the end of value, e.g. chop(1): 'Value' => 'Valu'; when applied to a list, chops characters from each list value, e.g. chop(1): ["travel", "beach"]=> ["trave", "beac"].
- chomp(x): Remove x characters from the beginning of value, e.g. chomp(1): ['Value'] => ['alue']; when applied to a list, removes characters from each list value, e.g. chomp(1): ["travel", "beach"]=> ["ravel", "each"].
- sort: Sort list of values, e.g. ['c', 'b', 'a'] => ['a', 'b', 'c'].
- rsort: Sort list of values in reverse order, e.g. ['a', 'b', 'c'] => ['c', 'b', 'a'].
- reverse: Reverse order of values, e.g. ['a', 'b', 'c'] => ['c', 'b', 'a'].
- uniq: Remove duplicate values, e.g. ['a', 'b', 'c', 'b', 'a'] => ['a', 'b', 'c'].
- join(x): Join list of values with delimiter x, e.g. join(:): ['a', 'b', 'c'] => 'a:b:c'; the DELIM option functions similar to join(x) but with DELIM, the join happens before being passed to any filters.
- append(x): Append x to list of values, e.g. append(d): ['a', 'b', 'c'] => ['a', 'b', 'c', 'd'].
- prepend(x): Prepend x to list of values, e.g. prepend(d): ['a', 'b', 'c'] => ['d', 'a', 'b', 'c'].
- remove(x): Remove x from list of values, e.g. remove(b): ['a', 'b', 'c'] => ['a', 'c'].

<!-- - shell_quote: Quotes the value for safe usage in the shell, e.g. My file.jpeg => 'My file.jpeg'; only adds quotes if needed.
- function: Run custom python function to filter value; use in format 'function:/path/to/file.py::function_name'. See example at https://github.com/RhetTbull/osxfiles/blob/master/examples/template_filter.py
-->

e.g. if file keywords are `["FOO","bar"]`:

- `"{exiftool:Keywords|lower}"` renders to `"foo", "bar"`
- `"{exiftool:Keywords|upper}"` renders to: `"FOO", "BAR"`
- `"{exiftool:Keywords|capitalize}"` renders to: `"Foo", "Bar"`
- `"{exiftool:Keywords|lower|parens}"` renders to: `"(foo)", "(bar)"`

e.g. if an image file description is "my description":

- `"{exiftool:Description|titlecase}"` renders to: `"My Description"`

**Find/Replace**

`[find,replace]`: optional text replacement to perform on rendered template value.  For example, to replace "/" in a a keyword, you could use the template `"{exiftool:Keywords[/,-]}"`.  Multiple replacements can be made by appending "|" and adding another find|replace pair.  e.g. to replace both "/" and ":" in keywords: `"{exiftool:Keywords[/,-|:,-]}"`.  find/replace pairs are not limited to single characters.  The "|" character cannot be used in a find/replace pair.

**Conditional Operators**

`conditional`: optional conditional expression that is evaluated as boolean (True/False) for use with the `?bool_value` modifier.  Conditional expressions take the form '` not operator value`' where `not` is an optional modifier that negates the `operator`.  Note: the space before the conditional expression is required if you use a conditional expression.  Valid comparison operators are:

- `contains`: template field contains value, similar to python's `in`
- `matches`: template field contains exactly value, unlike `contains`: does not match partial matches
- `startswith`: template field starts with value
- `endswith`: template field ends with value
- `<=`: template field is less than or equal to value
- `>=`: template field is greater than or equal to value
- `<`: template field is less than value
- `>`: template field is greater than value
- `==`: template field equals value
- `!=`: template field does not equal value

Multiple values may be separated by '|' (the pipe symbol) when used with `contains`, `matches`, `startswith`, and `endswith`.  `value` is itself a template statement so you can use one or more template fields in `value` which will be resolved before the comparison occurs. When applied to multi-valued fields (ie. lists), the comparison is applied to each value in the list and evaluates to True if *any* of the values match.

For example:

- `{exiftool:Keywords matches Beach}` resolves to True if 'Beach' is a keyword. It would not match keyword 'BeachDay'.
- `{exiftool:Keywords contains Beach}` resolves to True if any keyword contains the word 'Beach' so it would match both 'Beach' and 'BeachDay'.
- `{ISO < 100}` resolves to True if the file's ISO is < 100.
- `{exiftool:Keywords|lower contains beach}` uses the lower case filter to do case-insensitive matching to match any keyword that contains the word 'beach'.
- `{exiftool:Keywords|lower not contains beach}` uses the `not` modifier to negate the comparison so this resolves to True if there is no keyword that matches 'beach'.
- `{docx:author startswith John}` resolves to True if the author of a docx file starts with 'John'.
- `{audio:bitrate == 320}` resolves to True if the audio file's bitrate is 320 kbps.

**Boolean Values**

`?bool_value`: Template fields may be evaluated as boolean (True/False) by appending "?" after the field name or "[find/replace]".  If a field is True or has any value, the value following the "?" will be used to render the template instead of the actual field value.  If the template field evaluates to False or has no value (e.g. file has no title and field is `"{audio:title}"`) then the default value following a "," will be used.  

e.g. if file has a title

- `"{audio:title?I have a title,I do not have a title}"` renders to `"I have a title"`

and if it does not have a title: 

- `"{audio:title?I have a title,I do not have a title}"` renders to `"I do not have a title"`

**Default Values**

`,default`: optional default value to use if the template name has no value.  This modifier is also used for the value if False for boolean-type fields (see above) as well as to hold a sub-template for values like `{created.strftime}`.  If no default value provided and the field is null, autofile will use a default value of `'_'` (underscore character).

Template fields such as `created.strftime` use the default value to pass the template to use for `strftime`.  

e.g., if file date is 4 February 2020, 19:07:38,

- `"{created.strftime,%Y-%m-%d-%H%M%S}"` renders to `"2020-02-04-190738"`

**Special Characters**

If you want to include "{" or "}" in the output, use "{openbrace}" or "{closebrace}" template substitution.

e.g. `"{created.year}/{openbrace}{audio.title}{closebrace}"` would result in `"2020/{file Title}"`.

**Field Attributes**

Some templates have additional modifiers that can be appended to the template name using dot notation to access specific attributes of the template field. For example, the `{filepath}` template returns the path of the file being processed and `{filepath.parent}` returns the parent directory.

**Variables**

You can define variables for later use in the template string using the format `{var:NAME,VALUE}`.  Variables may then be referenced using the format `%NAME`. For example: `{var:foo,bar}` defines the variable `%foo` to have value `bar`. This can be useful if you want to re-use a complex template value in multiple places within your template string or for allowing the use of characters that would otherwise be prohibited in a template string. For example, the "pipe" (`|`) character is not allowed in a find/replace pair but you can get around this limitation like so: `{var:pipe,{pipe}}{audio:title[-,%pipe]}` which replaces the `-` character with `|` (the value of `%pipe`).  

Variables can also be referenced as fields in the template string, for example: `{var:year,created.year}{filepath.stem}-{%year}{filepath.suffix}`. In some cases, use of variables can make your template string more readable.  Variables can be used as template fields, as values for filters, as values for conditional operations, or as default values.  When used as a conditional value or default value, variables should be treated like any other field and enclosed in braces as conditional and default values are evaluated as template strings. For example: `{var:name,John}{docx:author contains {%name}?{%name},Not-{%name}}

If you need to use a `%` (percent sign character), you can escape the percent sign by using `%%`.  You can also use the `{percent}` template field where a template field is required. For example:

`{audio:title[:,%%]}` replaces the `:` with `%` and `{audio:title contains Foo?{audio:title}{percent},{audio:title}}` adds `%` to the audio title if it contains `Foo`. 