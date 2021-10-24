from setuptools import setup

setup(
    version="0.0.1",
    name="autofile-foo",
    install_requires="autofile",
    entry_points={"autofile": ["foo = autofile_foo"]},
    py_modules=["autofile_foo"],
)
