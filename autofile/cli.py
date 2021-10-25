""" Use template to automatically move files into directories """

import io
import pathlib
import re
import sys
from functools import partial
from typing import List, Optional

import click
from cloup import (
    Command,
    Context,
    HelpFormatter,
    HelpTheme,
    Style,
    argument,
    command,
    constraint,
    option,
    option_group,
    version_option,
)
from cloup.constraints import (
    ErrorFmt,
    If,
    RequireAtLeast,
    RequireExactly,
    mutually_exclusive,
    require_all,
)
from rich.console import Console
from rich.highlighter import NullHighlighter
from rich.markdown import Markdown
from yaspin import yaspin

from ._version import __version__
from .autofile import MultipleFilesError, process_files
from .constants import APP_NAME
from .renderoptions import RenderOptions
from .template import get_template_help
from .utils import bold, green, pluralize, red

# Set up rich console
_console = Console()
_console_stderr = Console(stderr=True)

# if True, shows verbose output, turned off via --quiet flag
_verbose = True


def verbose(message_str, **kwargs):
    if not _verbose:
        return
    _console.print(message_str, **kwargs)


def print_help_msg(command):
    with Context(command) as ctx:
        click.echo(command.get_help(ctx))


def print_error(message):
    """Print error message to stderr with rich"""
    _console_stderr.print(message, style="bold red")


def print_warning(message):
    """Print warning message to stdout with rich"""
    _console.print(message, style="bold yellow")


def echo(message):
    """print to stdout using rich"""
    _console.print(message)


# requires_one = RequireExactly(1).rephrased(
#     help="requires one",
#     error=f"it must be used with:\n" f"{ErrorFmt.param_list}",
# )


class AutofileCommand(Command):
    """Custom cloup.command that overrides get_help() to show additional help info for autofile"""

    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = HelpFormatter()

        formatter.write("\n\n")
        formatter.write(rich_text(bold("Template System"), width=formatter.width))
        formatter.write("\n\n")
        for help_item in get_template_help():
            # items from get_template_help are either markdown strings or lists of lists
            if type(help_item) is str:
                formatter.write(format_markdown_str(help_item, width=formatter.width))
                formatter.write("\n")
            elif isinstance(help_item, (tuple, list)):
                help_list = [tuple(rich_text(bold(col)) for col in help_item[0])]
                help_list.extend(tuple(h) for h in help_item[1:])
                formatter.write_dl(help_list)
                formatter.write("\n")
        formatter.write_text("")
        help_text += formatter.getvalue()
        return help_text

    def get_help_option(self, ctx: Context) -> Optional["click.Option"]:
        """Returns the help option object."""
        # copied from Click source code and modified to use pager
        help_options = self.get_help_option_names(ctx)

        if not help_options or not self.add_help_option:
            return None

        def show_help(ctx: Context, param: "click.Parameter", value: str) -> None:
            if value and not ctx.resilient_parsing:
                click.echo_via_pager(ctx.get_help(), color=ctx.color)
                ctx.exit()

        return click.Option(
            help_options,
            is_flag=True,
            is_eager=True,
            expose_value=False,
            callback=show_help,
            help="Show this message and exit.",
        )


formatter_settings = HelpFormatter.settings(
    theme=HelpTheme(
        invoked_command=Style(fg="bright_yellow"),
        heading=Style(fg="bright_white", bold=True),
        constraint=Style(fg="magenta"),
        col1=Style(fg="bright_yellow"),
    )
)


@command(cls=AutofileCommand, formatter_settings=formatter_settings)
@option_group(
    "Required",
    option(
        "--target",
        "-t",
        metavar="TARGET_DIRECTORY",
        help="Target destination directory.",
        type=click.Path(exists=True, file_okay=False, resolve_path=True),
    ),
    constraint=require_all,
)
@option_group(
    "Filing templates",
    option(
        "--directory",
        "-D",
        metavar="DIRECTORY_TEMPLATE",
        help="Directory template for exporting files.",
    ),
    option(
        "--filename",
        "-F",
        metavar="FILENAME_TEMPLATE",
        help="Filename template for exporting files.",
    ),
    constraint=RequireAtLeast(1),
)
@option_group(
    "Filter Options",
    option(
        "--glob",
        "-g",
        multiple=True,
        metavar="PATTERN",
        help="Filter files to process with a glob pattern, e.g. '--glob \"*.jpg\"' "
        "--glob may be repeated to use more than one pattern. "
        'Multiple patterns treated as "OR", that is, a file that matches one or more patterns will be processed. ',
    ),
    option(
        "--regex",
        "-r",
        multiple=True,
        metavar="PATTERN",
        help="Filter files to process with a regex pattern, e.g. '--regex \"IMG_[1-3].*\"' "
        "--regex may be repeated to use more than one pattern. "
        'Multiple patterns treated as "OR", that is, a file that matches one or more patterns will be processed. '
        "Any valid python regular express may be used.",
    ),
    option(
        "--filter",
        "-f",
        "filter_template",
        multiple=True,
        metavar="TEMPLATE_PATTERN",
        help="Filter files to process that match a metadata template pattern, e.g. '--filter \"{mdls:kMDItemKind contains image}\"'. "
        "--filter matches the file if TEMPLATE_PATTERN evaluates to a non-null value. "
        "--filter may be repeated to use more than one pattern. "
        'Multiple patterns treated as "OR", that is, a file that matches one or more patterns will be processed. ',
    ),
)
@option_group(
    "Options",
    option("--walk", "-w", is_flag=True, help="Recursively walk directories."),
    option("--quiet", "-Q", is_flag=True, help="Turn off verbose output."),
    option(
        "--plain",
        is_flag=True,
        help="Plain text mode.  Do not use rich output.",
        hidden=True,
    ),
    option("--copy", "-c", is_flag=True, help="Copy files instead of moving them."),
    option(
        "--hardlink", "-h", is_flag=True, help="Hardlink files instead of moving them."
    ),
    option(
        "--dry-run",
        "-d",
        is_flag=True,
        help="Dry run mode; do not actually move/copy any files.",
    ),
    # option(
    #     "--exiftool-path",
    #     type=click.Path(exists=True),
    #     default=get_exiftool_path(),
    #     help="Optional path to exiftool executable (will look in $PATH if not specified).",
    # )
)
@constraint(mutually_exclusive, ["copy", "hardlink"])
@version_option(version=__version__)
@argument(
    "files", nargs=-1, required=True, type=click.Path(exists=True, resolve_path=True)
)
def cli(
    directory,
    filename,
    target,
    walk,
    quiet,
    plain,
    copy,
    hardlink,
    dry_run,
    glob,
    regex,
    filter_template,
    files,
):
    """move or copy files into directories based on a template string"""

    # used to control whether to print out verbose output
    global _verbose
    _verbose = not quiet 

    if plain:
        # Plain text mode, disable rich output (used for testing)
        global _console
        global _console_stderr
        _console = Console(highlighter=NullHighlighter())
        _console_stderr = Console(stderr=True, highlighter=NullHighlighter())

    # create nice looking text for status
    filenames = [file for file in files if pathlib.Path(file).is_file()]
    dirnames = [file for file in files if pathlib.Path(file).is_dir()]
    text = f'Processing {len(filenames)} {pluralize(len(filenames),"file","files")}'
    dirtext = (
        f' and {len(dirnames)} {pluralize(len(dirnames), "directory","directories")}'
    )
    text = text + dirtext if walk else text
    if dirnames and not walk and not filenames:
        echo(f"Found 0 files{dirtext} but --walk was not specified, nothing to do")
        print_help_msg(cli)
        sys.exit(1)

    process_files_ = partial(
        process_files,
        target=target,
        directory_template=directory,
        filename_template=filename,
        walk=walk,
        copy=copy,
        hardlink=hardlink,
        dry_run=dry_run,
        glob=glob,
        regex=regex,
        filter_template=filter_template,
        verbose=verbose,
    )

    if not _verbose:
        with yaspin(text=text):
            try:
                files_processed = process_files_(files)
            except MultipleFilesError as e:
                print_error(
                    "Error: --directory or --filename template produced multiple target paths; cannot move file to more than one target path. "
                    "Change the template or use --copy or --hardlink: "
                    f"{e}"
                )
                sys.exit(1)
    else:
        verbose(text)
        try:
            files_processed = process_files_(files)
        except MultipleFilesError as e:
            print_error(
                "Error: --directory or --filename template produced multiple target paths; cannot move file to more than one target path. "
                "Change the template or use --copy or --hardlink: "
                f"{e}"
            )
            sys.exit(1)

    verbose(
        f"Done. Processed {files_processed} {pluralize(files_processed, 'file', 'files')}."
    )

    echo("Done.")


def rich_text(text, width=78):
    """Return rich formatted text"""
    sio = io.StringIO()
    console = Console(file=sio, force_terminal=True, width=width)
    console.print(text)
    rich_text = sio.getvalue()
    rich_text = rich_text.rstrip()
    sio.close()
    return rich_text


def strip_md_header_and_links(md):
    """strip markdown headers and links from markdown text md

    Args:
        md: str, markdown text

    Returns:
        str with markdown headers and links removed

    Note: This uses a very basic regex that likely fails on all sorts of edge cases
    but works for the links in the docs
    """
    links = r"(?:[*#])|\[(.*?)\]\(.+?\)"

    def subfn(match):
        return match.group(1)

    return re.sub(links, subfn, md)


def strip_md_links(md):
    """strip markdown links from markdown text md

    Args:
        md: str, markdown text

    Returns:
        str with markdown links removed

    Note: This uses a very basic regex that likely fails on all sorts of edge cases
    but works for the links in the osxphotos docs
    """
    links = r"\[(.*?)\]\(.+?\)"

    def subfn(match):
        return match.group(1)

    return re.sub(links, subfn, md)


def strip_html_comments(text):
    """Strip html comments from text (which doesn't need to be valid HTML)"""
    return re.sub(r"<!--(.|\s|\n)*?-->", "", text)


def format_markdown_str(string, width=78):
    """Return formatted markdown str for terminal"""
    sio = io.StringIO()
    console = Console(file=sio, force_terminal=True, width=width)
    console.print(Markdown(string))
    help_str = sio.getvalue()
    sio.close()
    return help_str


def main():
    cli()
