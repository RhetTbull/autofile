"""Test autofile CLI"""

import pathlib
from shutil import copyfile

import pytest
from click.testing import CliRunner

TEST_IMAGE_1 = "tests/test_files/pears.jpg"
TEST_IMAGE_2 = "tests/test_files/flowers.jpeg"
TEST_MP3_1 = "tests/test_files/warm_lights.mp3"


@pytest.fixture(scope="function")
def source(tmpdir_factory):
    cwd = pathlib.Path.cwd()
    tmpdir = pathlib.Path(tmpdir_factory.mktemp("data"))
    copyfile(cwd / TEST_IMAGE_1, tmpdir / pathlib.Path(TEST_IMAGE_1).name)
    copyfile(cwd / TEST_IMAGE_2, tmpdir / pathlib.Path(TEST_IMAGE_2).name)
    copyfile(cwd / TEST_MP3_1, tmpdir / pathlib.Path(TEST_MP3_1).name)

    return tmpdir


@pytest.fixture(scope="function")
def target(tmpdir_factory):
    return pathlib.Path(tmpdir_factory.mktemp("target"))


def test_cli_directory(source, target):
    """Test CLI with --directory"""
    from autofile.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--verbose",
            "--target",
            str(target),
            "--directory",
            "{created.year}",
            *[str(p) for p in source.glob("*")],
        ],
    )
    assert result.exit_code == 0
    for p in ["2021/flowers.jpeg", "2021/pears.jpg", "2021/warm_lights.mp3"]:
        target_file = target / p
        assert target_file.exists()
