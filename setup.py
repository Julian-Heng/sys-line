#!/usr/bin/env python3

import setuptools

setuptools.setup(
    name="sys-line",
    version="0.0.0",
    author="Julian Heng",
    author_email="julianhengwl@gmail.com",
    description="a simple status line generator",
    packages=setuptools.find_packages(),
    entry_points = {
        "console_scripts": ["sys-line = sys_line.__main__:main"]
    }
)
