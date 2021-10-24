import click
import cloup
import rich.traceback
from pluggy import HookimplMarker

hookimpl = HookimplMarker("autofile")


rich.traceback.install(show_locals=True, suppress=[click, cloup])
