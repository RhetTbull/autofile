#!/usr/bin/env python

import os.path
import sys

from setuptools import find_packages, setup

PACKAGE_NAME = "autofile"

if sys.version_info < (3, 8, 0):
    sys.stderr.write(f"ERROR: You need Python 3.8 or later to use {PACKAGE_NAME}.\n")
    exit(1)

# we'll import stuff from the source tree, let's ensure is on the sys path
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

# read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

about = {}
with open(
    os.path.join(this_directory, PACKAGE_NAME, "_version.py"),
    mode="r",
    encoding="utf-8",
) as f:
    exec(f.read(), about)

setup(
    name=PACKAGE_NAME,
    version=about["__version__"],
    description="Use templates to automatically move files into directories",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Rhet Turnbull",
    author_email="rturnbull+git@gmail.com",
    url="https://github.com/RhetTbull/autofile",
    project_urls={"GitHub": "https://github.com/RhetTbull/autofile"},
    download_url="https://github.com/RhetTbull/autofile",
    packages=find_packages(exclude=["tests", "utils"]),
    license="License :: OSI Approved :: MIT License",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=[
        "click>=8.0.1,<9.0.0",
        "cloup>=0.11.0,<0.14.0",
        "pathvalidate>=2.5.0,<3.0.0",
        "pdfminer.six>=20211012",
        "pluggy>=1.0.0,<=2.0.0",
        "python-docx>=0.8.11,<1.0.0",
        "rich>=11.0.0,<13.0.0",
        "tenacity==8.0.1",
        "textX>=2.3.0,<3.0.0",
        "tinytag>=1.8.0,<2.0.0",
        "yaspin>=2.1.0,<3.0.0",
    ]
    + (
        [
            "osxmetadata>=0.99.34,<1.0.0",
            "pyobjc-core>=7.3,<9.0",
            "pyobjc-framework-Cocoa>=7.3,<9.0",
            "pyobjc-framework-CoreServices>=7.3,<9.0",
            "pyobjc-framework-FSEvents>=7.3,<9.0",
        ]
        if sys.platform == "darwin"
        else []
    ),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            f"{PACKAGE_NAME}={PACKAGE_NAME}.cli:cli",
        ]
    },
    include_package_data=True,
)
