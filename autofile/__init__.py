import click
import cloup
import rich.traceback

from .hookspecs import hookimpl

rich.traceback.install(show_locals=True, suppress=[click, cloup])

from .autofile import process_files
from .renderoptions import RenderOptions
from .template import FileTemplate
