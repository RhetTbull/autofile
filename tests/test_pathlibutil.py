""" test FileUtil """

import os
import os.path
import pathlib
import tempfile

import pytest

import autofile.pathlibutil
from autofile.pathlibutil import SYSTEM, PathlibUtil

TEST_FILE = "tests/test_files/pears.jpg"
TEST_FILE_NAME = "pears.jpg"
TEST_DIR = "tests/test_files"

# if on macOS and pyobjc is installed, test the pyobjc methods
PYOBJC = False
try:
    import Foundation

    PYOBJC = True
except ImportError:
    pass


@pytest.mark.parametrize("pyobjc", [True, False])
def test_copy_file_valid(tmp_path, pyobjc, monkeypatch):
    """copy file with valid src, dest"""
    if PYOBJC:
        monkeypatch.setattr(PathlibUtil, "_pyobjc", pyobjc)
    result = PathlibUtil(TEST_FILE).copy_to(tmp_path)
    assert result.is_file()


@pytest.mark.parametrize("pyobjc", [True, False])
def test_copy_file_invalid(tmp_path, pyobjc, monkeypatch):
    """copy file with invalid src"""
    if PYOBJC:
        monkeypatch.setattr(PathlibUtil, "_pyobjc", pyobjc)
    with pytest.raises(Exception) as e:
        src = "tests/test_files/DOES_NOT_EXIST.jpg"
        assert PathlibUtil(src).copy_to(tmp_path)
    assert e.type == FileNotFoundError


@pytest.mark.parametrize("pyobjc", [True, False])
def test_copy_file_destination_file_exists(tmp_path, pyobjc, monkeypatch):
    """copy file when destination file exists"""
    if PYOBJC:
        monkeypatch.setattr(PathlibUtil, "_pyobjc", pyobjc)
    tmp_file = tmp_path / "test.jpg"
    tmp_file.touch()
    with pytest.raises(Exception) as e:
        assert PathlibUtil(TEST_FILE).copy_to(tmp_file)
    assert e.type == FileExistsError


@pytest.mark.parametrize("pyobjc", [True, False])
def test_copy_file_destination_is_dir(tmp_path, pyobjc, monkeypatch):
    """copy file when destination is a directory"""
    if PYOBJC:
        monkeypatch.setattr(PathlibUtil, "_pyobjc", pyobjc)
    dest_dir = tmp_path / "test_dir"
    dest_dir.mkdir()
    result = PathlibUtil(TEST_FILE).copy_to(dest_dir)
    assert result.is_file()


@pytest.mark.parametrize("pyobjc", [True, False])
def test_copy_file_source_is_dir(tmp_path, pyobjc, monkeypatch):
    """copy directory"""
    if PYOBJC:
        monkeypatch.setattr(PathlibUtil, "_pyobjc", pyobjc)
    result = PathlibUtil(TEST_DIR).copy_to(tmp_path)
    assert result.is_dir()
    assert TEST_FILE_NAME in [f.name for f in result.iterdir()]


@pytest.mark.parametrize("pyobjc", [True, False])
def test_copy_file_source_is_dir_dest_is_file(tmp_path, pyobjc, monkeypatch):
    """copy directory when destination is a file"""
    if PYOBJC:
        monkeypatch.setattr(PathlibUtil, "_pyobjc", pyobjc)
    tmp_file = tmp_path / "test.jpg"
    tmp_file.touch()
    with pytest.raises(Exception) as e:
        assert PathlibUtil(TEST_DIR).copy_to(tmp_file)
    assert e.type == FileExistsError


@pytest.mark.parametrize("pyobjc", [True, False])
def test_move_file_valid(tmp_path, pyobjc, monkeypatch):
    """move file with valid src, dest"""
    if PYOBJC:
        monkeypatch.setattr(PathlibUtil, "_pyobjc", pyobjc)
    src_path = tmp_path / "src"
    src_path.mkdir()
    dest_path = tmp_path / "dest"
    dest_path.mkdir()
    dest_path = dest_path / "test.jpg"
    src = PathlibUtil(TEST_FILE).copy_to(src_path)
    result = PathlibUtil(src).move_to(dest_path)
    assert result.is_file()


@pytest.mark.parametrize("pyobjc", [True, False])
def test_move_file_invalid(tmp_path, pyobjc, monkeypatch):
    """move file with invalid src"""
    if PYOBJC:
        monkeypatch.setattr(PathlibUtil, "_pyobjc", pyobjc)
    with pytest.raises(Exception) as e:
        src = "tests/test_files/DOES_NOT_EXIST.jpg"
        assert PathlibUtil(src).move_to(tmp_path)
    assert e.type == FileNotFoundError


@pytest.mark.parametrize("pyobjc", [True, False])
def test_move_file_destination_file_exists(tmp_path, pyobjc, monkeypatch):
    """move file when destination file exists"""
    if PYOBJC:
        monkeypatch.setattr(PathlibUtil, "_pyobjc", pyobjc)
    src_path = tmp_path / "src"
    src_path.mkdir()
    dest_path = tmp_path / "dest"
    dest_path.mkdir()
    dest_path = dest_path / "test.jpg"
    dest_path.touch()
    src = PathlibUtil(TEST_FILE).copy_to(src_path)
    with pytest.raises(Exception) as e:
        assert PathlibUtil(src).move_to(dest_path)
    assert e.type == FileExistsError


@pytest.mark.parametrize("pyobjc", [True, False])
def test_move_file_destination_is_dir(tmp_path, pyobjc, monkeypatch):
    """move file when destination is a directory"""
    if PYOBJC:
        monkeypatch.setattr(PathlibUtil, "_pyobjc", pyobjc)
    src_path = tmp_path / "src"
    src_path.mkdir()
    dest_path = tmp_path / "dest"
    dest_path.mkdir()
    src = PathlibUtil(TEST_FILE).copy_to(src_path)
    result = PathlibUtil(src).move_to(dest_path)
    assert result.is_file()


@pytest.mark.parametrize("pyobjc", [True, False])
def test_move_file_source_is_dir(tmp_path, pyobjc, monkeypatch):
    """move directory"""
    if PYOBJC:
        monkeypatch.setattr(PathlibUtil, "_pyobjc", pyobjc)
    src_path = tmp_path / "src"
    src_path.mkdir()
    dest_path = tmp_path / "dest"
    dest_path.mkdir()
    PathlibUtil(TEST_FILE).copy_to(src_path)
    result = PathlibUtil(src_path).move_to(dest_path)
    assert result.is_dir()
    assert TEST_FILE_NAME in [f.name for f in result.iterdir()]


@pytest.mark.parametrize("pyobjc", [True, False])
def test_move_file_source_is_dir_dest_is_file(tmp_path, pyobjc, monkeypatch):
    """move directory when destination is a file"""
    if PYOBJC:
        monkeypatch.setattr(PathlibUtil, "_pyobjc", pyobjc)
    src_path = tmp_path / "src"
    src_path.mkdir()
    dest_path = tmp_path / "dest"
    dest_path.mkdir()
    dest_path = dest_path / "test.jpg"
    dest_path.touch()
    PathlibUtil(TEST_FILE).copy_to(src_path)
    with pytest.raises(Exception) as e:
        assert PathlibUtil(src_path).move_to(dest_path)
    assert e.type == FileExistsError


def test_mkdir(tmp_path):
    """mkdir"""
    dest = tmp_path / "foo"
    result = PathlibUtil(dest).mkdir()
    assert result.is_dir()


def test_mkdir_file_exists(tmp_path):
    """mkdir"""
    dest = tmp_path / "foo"
    dest.touch()
    with pytest.raises(Exception) as e:
        assert PathlibUtil(dest).mkdir()
    assert e.type == FileExistsError


def test_hardlink_to_file_valid(tmp_path):
    """hardlink_to file with valid src, dest"""
    dest = tmp_path / "test.jpg"
    result = PathlibUtil(dest).hardlink_to(TEST_FILE)
    assert result.is_file()
    assert result.samefile(TEST_FILE)


def test_hardlink_to_file_invvalid(tmp_path):
    """hardlink_to file with invalid src, dest"""
    dest = tmp_path / "test.jpg"
    dest2 = tmp_path / "test2.jpg"
    with pytest.raises(Exception) as e:
        assert PathlibUtil(dest).hardlink_to(dest2)
    assert e.type == FileNotFoundError


def test_hardlink_at_file_valid(tmp_path):
    """hardlink_at file with valid src, dest"""
    dest = tmp_path / "test.jpg"
    result = PathlibUtil(TEST_FILE).hardlink_at(dest)
    assert result.is_file()
    assert result.samefile(dest)


def test_hardlink_at_file_invvalid(tmp_path):
    """hardlink_to file with invalid src, dest"""
    dest = tmp_path / "test.jpg"
    dest2 = tmp_path / "test2.jpg"
    with pytest.raises(Exception) as e:
        assert PathlibUtil(dest).hardlink_at(dest2)
    assert e.type == FileNotFoundError


# def test_unlink_file():
#     temp_dir = tempfile.TemporaryDirectory(prefix="autofile_")
#     src = "tests/test-images/wedding.jpg"
#     dest = os.path.join(temp_dir.name, "wedding.jpg")
#     result = FileUtil.copy(src, temp_dir.name)
#     assert os.path.isfile(dest)
#     FileUtil.unlink(dest)
#     assert not os.path.isfile(dest)


# def test_rmdir():
#     temp_dir = tempfile.TemporaryDirectory(prefix="autofile_")
#     dir_name = temp_dir.name
#     assert os.path.isdir(dir_name)
#     FileUtil.rmdir(dir_name)
#     assert not os.path.isdir(dir_name)


# def test_rename_file():
#     # rename file with valid src, dest
#     temp_dir = tempfile.TemporaryDirectory(prefix="autofile_")
#     src = "tests/test-images/wedding.jpg"
#     dest = f"{temp_dir.name}/foo.jpg"
#     dest2 = f"{temp_dir.name}/bar.jpg"
#     FileUtil.copy(src, dest)
#     result = FileUtil.rename(dest, dest2)
#     assert result
#     assert pathlib.Path(dest2).exists()
#     assert not pathlib.Path(dest).exists()


# def test_move_file():
#     """move file with valid src, dest"""
#     assert False


# def test_move_file_dest_exists():
#     """move file with dest that exists"""
#     assert False
