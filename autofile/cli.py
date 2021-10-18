""" Use template to automatically move files into directories """

import datetime
import os
import pathlib
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
from rich.traceback import install
from yaspin import yaspin

from ._version import __version__
from .constants import APP_NAME
from .renderoptions import RenderOptions
from .template import FileTemplate
from .utils import green, pluralize, red

# Set up rich console
_console = Console()
_console_stderr = Console(stderr=True)

# if True, shows verbose output, controlled via --verbose flag
_verbose = False


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
        formatter.write_text("")
        help_text += formatter.getvalue()
        return help_text


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
    "Options",
    option("--walk", "-w", is_flag=True, help="Recursively walk directories."),
    option("--verbose", "-V", "verbose_", is_flag=True, help="Show verbose output."),
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
    verbose_,
    plain,
    copy,
    hardlink,
    dry_run,
    files,
):
    """move or copy files into directories based on a template string"""

    # install rich traceback output
    install(show_locals=True)

    # used to control whether to print out verbose output
    global _verbose
    _verbose = verbose_

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
    )

    if not _verbose:
        with yaspin(text=text):
            files_processed = process_files_(files)
    else:
        verbose(text)
        files_processed = process_files_(files)

    verbose(
        f"Done. Processed {files_processed} {pluralize(files_processed, 'file', 'files')}."
    )

    echo("Done.")


def process_files(
    files,
    target: str,
    directory_template: Optional[str] = None,
    filename_template: Optional[str] = None,
    walk: bool = False,
    copy: bool = False,
    hardlink: bool = False,
    dry_run: bool = False,
) -> int:
    """Process files"""
    files_processed = 0
    for filename in files:
        file = pathlib.Path(filename)
        if file.is_dir():
            if walk:
                verbose(f"Processing directory {file}")
                files_processed += process_files(
                    file.iterdir(), walk=walk, dry_run=dry_run
                )
            else:
                verbose(f"Skipping directory {file}")
        else:
            verbose(f"Processing file {file}")
            options = RenderOptions()
            template = FileTemplate(filename)
            results = template.render(directory_template, options=options)
            print(results)
            files_processed += 1
    return files_processed


def main():
    cli()
