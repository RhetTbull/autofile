"""Automatically file files based on metadata templates"""
import fnmatch
import pathlib
import re
from typing import Callable, List, Optional

from .constants import NONE_STR_SENTINEL
from .renderoptions import RenderOptions
from .template import FileTemplate
from .utils import noop


def filter_file(
    filepath: pathlib.Path,
    glob: Optional[List[str]] = None,
    regex: Optional[List[str]] = None,
    filter_template: Optional[List[str]] = None,
) -> bool:
    """Return True if filepath matches one or more filters, otherwise False"""
    if not glob and not regex and not filter_template:
        return True

    glob_match = False
    if glob:
        glob_match = any(fnmatch.fnmatch(filepath.name, pattern) for pattern in glob)

    regex_match = False
    if regex:
        regex_match = any(re.search(pattern, filepath.name) for pattern in regex)

    filter_match = False
    if filter_template:
        options = RenderOptions(none_str=NONE_STR_SENTINEL)
        for pattern in filter_template:
            results, _ = FileTemplate(filepath).render(pattern, options=options)
            if results and all(NONE_STR_SENTINEL not in result for result in results):
                filter_match = True
                break

    return (
        (glob_match if glob else True)
        and (regex_match if regex else True)
        and (filter_match if filter_template else True)
    )


def process_files(
    files,
    target: str,
    directory_template: Optional[str] = None,
    filename_template: Optional[str] = None,
    walk: bool = False,
    copy: bool = False,
    hardlink: bool = False,
    dry_run: bool = False,
    glob: Optional[List[str]] = None,
    regex: Optional[List[str]] = None,
    filter_template: Optional[List[str]] = None,
    verbose: Optional[Callable] = None,
) -> int:
    """Process files"""
    verbose = verbose or noop

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
            if not filter_file(file, glob, regex, filter_template):
                verbose(f"Skipping file {file}")
                continue
            verbose(f"Processing file {file}")
            options = RenderOptions()
            template = FileTemplate(filename)
            results, _ = template.render(directory_template, options=options)
            print(results)
            files_processed += 1
    return files_processed
