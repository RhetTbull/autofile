"""Utils for photos_time_warp"""


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
    """Return red string in rich markdown"""
    return f"[red]{msg}[/red]"


def green(msg: str) -> str:
    """Return green string in rich markdown"""
    return f"[green]{msg}[/green]"
