""" FileUtil class with methods for copy, hardlink, unlink, etc. Works with pathlib.Path """

import pathlib
import platform
import shutil
import os

# python version as 2-digit float (e.g. 3.7)
PY_VERSION = float(".".join(platform.python_version_tuple()[:2]))
SYSTEM = platform.system()
PYOBJC = False

if SYSTEM == "Darwin":
    try:
        import Foundation

        PYOBJC = True
    except ImportError:
        pass


class PathlibUtil:
    """Various file utilities based on pathlib.Path"""

    def __init__(self, path):
        self.path = pathlib.Path(path)

    def __getattr__(self, attr):
        # delegate to pathlib.Path
        return_value = getattr(self.path, attr)
        if isinstance(return_value, pathlib.Path):
            return PathlibUtil(return_value)
        return return_value

    def copy_to(self, dest):
        """Copies a file or directory from src path to dest path

        Args:
            dest: destination path as string
                  dest may be either directory or file; in either case, src file/directory must not exist in dest
            Note: src and dest may be either a string or a pathlib.Path object

        Returns:
            PathLibUtil object of the new file/directory

        Raises:
            OSError if copy fails
            FileExistsError if dest already exists
            FileNotFoundError if src does not exist
        """
        if not isinstance(dest, PathlibUtil):
            dest = PathlibUtil(dest)

        if not self.path.exists():
            raise FileNotFoundError(f"{self.path} does not exist")

        if dest.is_file():
            raise FileExistsError(f"{dest} already exists")

        if dest.is_dir():
            dest = dest / self.path.name

        if self._pyobjc:
            return self._copy_to_mac(dest)

        if self.path.is_dir():
            shutil.copytree(str(self.path), str(dest))
        else:
            shutil.copy2(str(self.path), str(dest))

        return dest

    def _copy_to_mac(self, dest):
        """copy_to implementation that uses NSFileManager to take advantage of copy on write for APFS

        If the source is a directory, this method copies the directory and all of its contents, including any hidden files
        """
        src = self.path
        error = Foundation.NSFileManager.defaultManager().copyItemAtPath_toPath_error_(
            str(src), str(dest), None
        )
        # error is a tuple of (bool, error_string)
        # error[0] is True if copy succeeded
        if not error[0]:
            raise OSError(error[1])
        return dest

    def move_to(self, dest):
        """Move file or directory to dest"""
        if not isinstance(dest, PathlibUtil):
            dest = PathlibUtil(dest)

        if not self.path.exists():
            raise FileNotFoundError(f"{self.path} does not exist")

        if dest.is_file():
            raise FileExistsError(f"{dest} already exists")

        if dest.is_dir():
            dest = dest / self.path.name

        if self._pyobjc:
            return self._move_to_mac(dest)

        shutil.move(str(self.path), str(dest))
        return dest

    def _move_to_mac(self, dest):
        """move_to implementation that uses NSFileManager

        If the source is a directory, this method moves the directory and all of its contents, including any hidden files
        """
        src = self.path
        error = Foundation.NSFileManager.defaultManager().moveItemAtPath_toPath_error_(
            str(src), str(dest), None
        )
        # error is a tuple of (bool, error_string)
        # error[0] is True if copy succeeded
        if not error[0]:
            raise OSError(error[1])
        return dest

    def mkdir(self):
        """Create directory at this path"""
        # pathlib.Path().mkdir returns None but we want to return the new path
        self.path.mkdir()
        return self

    def hardlink_to(self, target):
        """Make this path a hard link to the same file as target (opposite of hardlink_at)"""
        # This is included in Python 3.10 but not earlier
        if not isinstance(target, PathlibUtil):
            target = PathlibUtil(target)

        if self.path.exists():
            raise FileExistsError(f"{self.path} already exists")

        if not target.exists():
            raise FileNotFoundError(f"{target} does not exist")

        os.link(str(target), str(self.path))
        return self

    def hardlink_at(self, dest):
        """Make dest a hardlink to this path (opposite of hardlink_to)"""
        if not isinstance(dest, PathlibUtil):
            dest = PathlibUtil(dest)

        if dest.exists():
            raise FileExistsError(f"{dest} already exists")

        if not self.path.exists():
            raise FileNotFoundError(f"{self.path} does not exist")

        return dest.hardlink_to(self.path)

    @property
    def _pyobjc(self):
        return PYOBJC

    def __str__(self):
        return self.path.__str__()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.path})"

    def __truediv__(self, key):
        try:
            return self.path._make_child((key,))
        except TypeError:
            return NotImplemented

    def __rtruediv__(self, key):
        try:
            return self.path._from_parts([key] + self._parts)
        except TypeError:
            return NotImplemented

    # @classmethod
    # def unlink(cls, filepath):
    #     """unlink filepath; if it's pathlib.Path, use Path.unlink, otherwise use os.unlink"""
    #     if isinstance(filepath, pathlib.Path):
    #         filepath.unlink()
    #     else:
    #         os.unlink(filepath)

    # @classmethod
    # def rmdir(cls, dirpath):
    #     """remove directory filepath; dirpath must be empty"""
    #     if isinstance(dirpath, pathlib.Path):
    #         dirpath.rmdir()
    #     else:
    #         os.rmdir(dirpath)

    # @classmethod
    # def utime(cls, path, times):
    #     """Set the access and modified time of path."""
    #     os.utime(path, times)

    # @classmethod
    # def cmp(cls, f1, f2, mtime1=None):
    #     """Does shallow compare (file signatures) of f1 to file f2.
    #     Arguments:
    #     f1 --  File name
    #     f2 -- File name
    #     mtime1 -- optional, pass alternate file modification timestamp for f1; will be converted to int

    #     Return value:
    #     True if the file signatures as returned by stat are the same, False otherwise.
    #     Does not do a byte-by-byte comparison.
    #     """

    #     s1 = cls._sig(os.stat(f1))
    #     if mtime1 is not None:
    #         s1 = (s1[0], s1[1], int(mtime1))
    #     s2 = cls._sig(os.stat(f2))
    #     if s1[0] != stat.S_IFREG or s2[0] != stat.S_IFREG:
    #         return False
    #     return s1 == s2

    # @classmethod
    # def cmp_file_sig(cls, f1, s2):
    #     """Compare file f1 to signature s2.
    #     Arguments:
    #     f1 --  File name
    #     s2 -- stats as returned by _sig

    #     Return value:
    #     True if the files are the same, False otherwise.
    #     """

    #     if not s2:
    #         return False

    #     s1 = cls._sig(os.stat(f1))

    #     if s1[0] != stat.S_IFREG or s2[0] != stat.S_IFREG:
    #         return False
    #     return s1 == s2

    # @classmethod
    # def file_sig(cls, f1):
    #     """return os.stat signature for file f1"""
    #     return cls._sig(os.stat(f1))

    # @classmethod
    # def rename(cls, src, dest):
    #     """Copy src to dest

    #     Args:
    #         src: path to source file
    #         dest: path to destination file

    #     Returns:
    #         Name of renamed file (dest)

    #     """
    #     os.rename(str(src), str(dest))
    #     return dest

    # @staticmethod
    # def _sig(st):
    #     """return tuple of (mode, size, mtime) of file based on os.stat
    #     Args:
    #         st: os.stat signature
    #     """
    #     # use int(st.st_mtime) because ditto does not copy fractional portion of mtime
    #     return (stat.S_IFMT(st.st_mode), st.st_size, int(st.st_mtime))
