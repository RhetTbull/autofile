"""Automatically file files based on metadata templates"""
import fnmatch
import pathlib
import re
from typing import Callable, List, Optional

from .constants import NONE_STR_SENTINEL
from .pathlibutil import PathlibUtil
from .renderoptions import RenderOptions
from .template import FileTemplate, UnknownFieldError
from .utils import noop


class MultipleFilesError(Exception):
    """Multiple files found"""

    pass


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
    dir_options = RenderOptions(dirname=True)
    file_options = RenderOptions(filename=True)

    files_processed = 0
    for filename in files:
        file = PathlibUtil(filename)
        if file.is_dir():
            if walk:
                verbose(f"Processing directory {file}")
                files_processed += process_files(
                    file.iterdir(),
                    target=target,
                    directory_template=directory_template,
                    filename_template=filename_template,
                    walk=walk,
                    copy=copy,
                    hardlink=hardlink,
                    dry_run=dry_run,
                    glob=glob,
                    regex=regex,
                    filter_template=filter_template,
                    verbose=verbose,
                )
            else:
                verbose(f"Skipping directory {file}")
        else:
            if not filter_file(file, glob, regex, filter_template):
                verbose(f"Skipping file {file}")
                continue
            target_path = pathlib.Path(target)

            rendered_directories = []
            if directory_template:
                rendered_directories, _ = FileTemplate(filename).render(
                    directory_template, options=dir_options
                )
                if len(rendered_directories) > 1 and not (any([copy, hardlink])):
                    raise MultipleFilesError(f"{rendered_directories}")

            rendered_filenames = []
            if filename_template:
                rendered_filenames, _ = FileTemplate(filename).render(
                    filename_template, options=file_options
                )
                if (len(rendered_filenames) > 1) and not (any([copy, hardlink])):
                    raise MultipleFilesError(f"{rendered_filenames}")

            # build target paths
            target_paths = [target_path]
            if rendered_directories:
                target_paths = [
                    target_path / directory for directory in rendered_directories
                ]
            if rendered_filenames:
                target_paths = [
                    target_path / filename
                    for target_path in target_paths
                    for filename in rendered_filenames
                ]
            else:
                target_paths = [target_path / file.name for target_path in target_paths]

            # move, copy, or hardlink files
            for target_path in target_paths:
                action = "Copying" if copy else "Hardlinking" if hardlink else "Moving"
                verbose(f"{action} {file} to {target_path}")
                if not dry_run:
                    if not target_path.parent.exists():
                        target_path.parent.mkdir(parents=True)
                    if hardlink:
                        file.hardlink_at(target_path)
                    elif copy:
                        file.copy_to(target_path)
                    else:
                        file.move_to(target_path)

            files_processed += 1
    return files_processed
