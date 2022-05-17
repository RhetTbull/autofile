"""Test autofile CLI"""

import pathlib
import re
from os import stat, utime
from shutil import copyfile

import pytest
from click.testing import CliRunner

TEST_IMAGE_1 = "tests/test_files/pears.jpg"
TEST_IMAGE_2 = "tests/test_files/flowers.jpeg"
TEST_MP3_1 = "tests/test_files/warm_lights.mp3"


def copy_file(source, target):
    """Copy a file while preserving the original timestamp"""
    copyfile(source, target)
    stats = stat(str(source))
    utime(str(target), (stats.st_atime, stats.st_mtime))


@pytest.fixture(scope="function")
def source(tmpdir_factory):
    cwd = pathlib.Path.cwd()
    tmpdir = pathlib.Path(tmpdir_factory.mktemp("data"))
    copy_file(cwd / TEST_IMAGE_1, tmpdir / pathlib.Path(TEST_IMAGE_1).name)
    copy_file(cwd / TEST_IMAGE_2, tmpdir / pathlib.Path(TEST_IMAGE_2).name)
    copy_file(cwd / TEST_MP3_1, tmpdir / pathlib.Path(TEST_MP3_1).name)

    return tmpdir


@pytest.fixture(scope="function")
def target(tmpdir_factory):
    return pathlib.Path(tmpdir_factory.mktemp("target"))


def test_cli_directory(source, target):
    """Test CLI with --directory"""
    from autofile.cli import cli

    source_files = list(source.glob("*"))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--target",
            str(target),
            "--directory",
            "{filepath.suffix|chomp(1)}",
            *[str(p) for p in source_files],
        ],
    )
    assert result.exit_code == 0
    assert "Moving" in result.output
    for p in ["jpeg/flowers.jpeg", "jpg/pears.jpg", "mp3/warm_lights.mp3"]:
        target_file = target / p
        assert target_file.exists()
    # Check that source files don't exist (they got moved)
    for p in source_files:
        assert not p.exists()


def test_cli_directory_dry_run(source, target):
    """Test CLI with --directory with --dry-run"""
    from autofile.cli import cli

    source_files = list(source.glob("*"))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--dry-run",
            "--target",
            str(target),
            "--directory",
            "{filepath.suffix|chomp(1)}",
            *[str(p) for p in source_files],
        ],
    )
    assert result.exit_code == 0
    assert "Moving" in result.output
    for p in ["jpeg/flowers.jpeg", "jpg/pears.jpg", "mp3/warm_lights.mp3"]:
        target_file = target / p
        assert not target_file.exists()
    # Check that source files exist (they did not get moved)
    for p in source_files:
        assert p.exists()


def test_cli_directory_copy(source, target):
    """Test CLI with --directory and --copy"""
    from autofile.cli import cli

    source_files = list(source.glob("*"))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--target",
            str(target),
            "--copy",
            "--directory",
            "{filepath.suffix|chomp(1)}",
            *[str(p) for p in source_files],
        ],
    )
    assert result.exit_code == 0
    assert "Copying" in result.output
    for p in ["jpeg/flowers.jpeg", "jpg/pears.jpg", "mp3/warm_lights.mp3"]:
        target_file = target / p
        assert target_file.exists()
    # Check that source files didn't get moved
    for p in source_files:
        assert p.exists()


def test_cli_directory_hardlink(source, target):
    """Test CLI with --directory and --hardlink"""
    from autofile.cli import cli

    source_files = list(source.glob("*"))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--target",
            str(target),
            "--hardlink",
            "--directory",
            "{filepath.suffix|chomp(1)}",
            *[str(p) for p in source_files],
        ],
    )
    assert result.exit_code == 0
    assert "Hardlinking" in result.output
    for p in ["jpeg/flowers.jpeg", "jpg/pears.jpg", "mp3/warm_lights.mp3"]:
        target_file = target / p
        assert target_file.exists()
        source_file = [s for s in source_files if s.name == target_file.name][0]
        assert target_file.samefile(source_file)
    # Check that source files didn't get moved
    for p in source_files:
        assert p.exists()


def test_cli_directory_walk(source, target):
    """Test CLI with --directory and --walk"""
    from autofile.cli import cli

    source_files = list(source.glob("*"))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--target",
            str(target),
            "--directory",
            "{filepath.suffix|chomp(1)}",
            "--walk",
            str(source),
        ],
    )
    assert result.exit_code == 0
    assert "Moving" in result.output
    for p in ["jpeg/flowers.jpeg", "jpg/pears.jpg", "mp3/warm_lights.mp3"]:
        target_file = target / p
        assert target_file.exists()
    # Check that source files don't exist (they got moved)
    for p in source_files:
        assert not p.exists()


def test_cli_directory_glob(source, target):
    """Test CLI with --directory"""
    from autofile.cli import cli

    source_files = list(source.glob("*"))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--target",
            str(target),
            "--directory",
            "{audio:artist}",
            "--glob",
            "*.mp3",
            *[str(p) for p in source_files],
        ],
    )
    assert result.exit_code == 0
    assert "Moving" in result.output
    for p in ["Darkroom/warm_lights.mp3"]:
        target_file = target / p
        assert target_file.exists()
    # Check that source files don't exist (they got moved)
    for p in source_files:
        if p.name == "warm_lights.mp3":
            assert not p.exists()


def test_cli_filename(source, target):
    """Test CLI with --filename"""
    from autofile.cli import cli

    source_files = list(source.glob("*"))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--target",
            str(target),
            "--filename",
            "{filepath.suffix|chomp(1)}-{filepath.name}",
            *[str(p) for p in source_files],
        ],
    )
    assert result.exit_code == 0
    assert "Moving" in result.output
    for p in ["jpeg-flowers.jpeg", "jpg-pears.jpg", "mp3-warm_lights.mp3"]:
        target_file = target / p
        assert target_file.exists()
    # Check that source files don't exist (they got moved)
    for p in source_files:
        assert not p.exists()


def test_cli_filename_directory(source, target):
    """Test CLI with --filename with --directory"""
    from autofile.cli import cli

    source_files = list(source.glob("*"))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--target",
            str(target),
            "--filename",
            "{filepath.suffix|chomp(1)}-{filepath.name}",
            "--directory",
            "{exiftool:Make}",
            *[str(p) for p in source_files],
        ],
    )
    assert result.exit_code == 0
    assert "Moving" in result.output
    for p in [
        "Apple/jpeg-flowers.jpeg",
        "Apple/jpg-pears.jpg",
        "_/mp3-warm_lights.mp3",
    ]:
        target_file = target / p
        assert target_file.exists()
    # Check that source files don't exist (they got moved)
    for p in source_files:
        assert not p.exists()


def test_cli_filename_directory_filter(source, target):
    """Test CLI with --filename with --directory"""
    from autofile.cli import cli

    source_files = list(source.glob("*"))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--plain",
            "--target",
            str(target),
            "--filename",
            "{filepath.suffix|chomp(1)}-{filepath.name}",
            "--directory",
            "{exiftool:Make}",
            "--filter",
            "{exiftool:Make matches Apple}",
            *[str(p) for p in source_files],
        ],
    )
    assert result.exit_code == 0
    output = str(result.output)
    assert "Moving" in output

    # TODO: these pass with pytest -s but otherwise fail
    # assert re.findall("Skipping.*warm_lights.mp3", output)

    assert "Processed 2" in output

    for p in ["Apple/jpeg-flowers.jpeg", "Apple/jpg-pears.jpg"]:
        target_file = target / p
        assert target_file.exists()
    for p in ["_/mp3-warm_lights.mp3"]:
        target_file = target / p
        assert not target_file.exists()
    # Check that source files don't exist (they got moved)
    for p in source_files:
        if p.suffix != ".mp3":
            assert not p.exists()
        else:
            assert p.exists()


def test_cli_directory_regex(source, target):
    """Test CLI with --regex"""
    from autofile.cli import cli

    source_files = list(source.glob("*"))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--plain",
            "--target",
            str(target),
            "--directory",
            "{filepath.suffix|chomp(1)}",
            "--regex",
            r".*\.jpg",
            *[str(p) for p in source_files],
        ],
    )
    assert result.exit_code == 0
    output = str(result.output)
    assert "Moving" in output
    for p in ["jpg/pears.jpg"]:
        target_file = target / p
        assert target_file.exists()

    # TODO: these pass with pytest -s but otherwise fail
    # assert re.findall(r"Skipping.*flowers.jpeg", output)
    # assert re.findall(r"Skipping.*warm_lights.mp3", output)
    assert "Processed 1" in output

    # Check that source files don't exist (they got moved)
    for p in source_files:
        if p.name == "pears.jpg":
            assert not p.exists()
        else:
            assert p.exists()


def test_cli_directory_quiet(source, target):
    """Test CLI with --quiet"""
    from autofile.cli import cli

    source_files = list(source.glob("*"))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--quiet",
            "--target",
            str(target),
            "--directory",
            "{filepath.suffix|chomp(1)}",
            *[str(p) for p in source_files],
        ],
    )
    assert result.exit_code == 0
    assert "Moving" not in result.output
    for p in ["jpeg/flowers.jpeg", "jpg/pears.jpg", "mp3/warm_lights.mp3"]:
        target_file = target / p
        assert target_file.exists()
    # Check that source files don't exist (they got moved)
    for p in source_files:
        assert not p.exists()
