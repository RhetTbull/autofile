import click
import cloup
import rich.traceback

from .autofile import process_files
from .template import FileTemplate

rich.traceback.install(show_locals=True, suppress=[click, cloup])
