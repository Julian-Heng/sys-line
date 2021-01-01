#!/usr/bin/env python3

# sys-line - a simple status line generator
# Copyright (C) 2019-2020  Julian Heng
#
# This file is part of sys-line.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import setuptools

from pathlib import Path


class CleanCommand(setuptools.Command):

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        def find_files(path, pattern, files):
            for j in Path(path).glob(pattern):
                if j.is_dir():
                    find_files(j, "*", files)
                files.append(j)

        patterns = ("build", "dist", "*.pyc", "*.tgz", "*.egg-info")
        files = list()

        for pattern in patterns:
            find_files(".", pattern, files)

        for i in files:
            if i.is_dir():
                print(f"removed directory '{i}'")
                i.rmdir()
            else:
                print(f"removed '{i}'")
                i.unlink()


setuptools.setup(
    name="sys-line",
    version="0.0.0",
    description="a simple status line generator",
    url="https://www.gitlab.com/julian-heng/sys-line",
    author="Julian Heng",
    author_email="julianhengwl@gmail.com",
    license="GPL",
    classifiers=[
        "Development Status :: 3 - Alpha",

        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",

        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: BSD :: FreeBSD",

        "License :: OSI Approved :: GNU General Public License v3 or later "
        "(GPLv3+)",
    ],
    keywords="system status",
    project_urls={
        "Source": "https://www.gitlab.com/julian-heng/sys-line",
    },
    packages=setuptools.find_packages(".", exclude=["*.test"]),
    package_dir={"": "."},
    python_requires=">=3.6",
    entry_points={
        "console_scripts": ["sys-line = sys_line.__main__:main"]
    },
    cmdclass={"clean": CleanCommand},
)
