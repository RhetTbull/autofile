"""Utils for autofile"""

import platform


def pluralize(count, singular, plural):
    """Return singular or plural based on count"""
    if count == 1:
        return singular
    else:
        return plural


def noop(*args, **kwargs):
    """No-op function for use as verbose if verbose not set"""
    pass


def red(msg: str) -> str:
    """Return red string in rich markup"""
    return f"[red]{msg}[/red]"


def green(msg: str) -> str:
    """Return green string in rich markup"""
    return f"[green]{msg}[/green]"


def bold(msg: str) -> str:
    """Return bold string in rich markup"""
    return f"[bold]{msg}[/bold]"


def get_os_version():
    # returns tuple of str containing OS version
    # e.g. 10.13.6 = ("10", "13", "6")
    version = platform.mac_ver()[0].split(".")
    if len(version) == 2:
        (ver, major) = version
        minor = "0"
    elif len(version) == 3:
        (ver, major, minor) = version
    else:
        raise (
            ValueError(
                f"Could not parse version string: {platform.mac_ver()} {version}"
            )
        )
    return (ver, major, minor)
