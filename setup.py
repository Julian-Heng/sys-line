#!/usr/bin/env python3

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

        patterns = ("build", "dist", "*.pyc", "*.tgz", "src/*.egg-info")
        files = list()

        for pattern in patterns:
            find_files(".", pattern, files)

        for i in files:
            if i.is_dir():
                print("removed directory '{}'".format(i))
                i.rmdir()
            else:
                print("removed '{}'".format(i))
                i.unlink()


setuptools.setup(
    name="sys-line",
    version="0.0.0",
    description="a simple status line generator",
    url="https://www.gitlab.com/julian-heng/sys-line",
    author="Julian Heng",
    author_email="julianhengwl@gmail.com",
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
    ],
    keywords="system status",
    project_urls={
        "Source": "https://www.gitlab.com/julian-heng/sys-line",
    },
    packages=setuptools.find_packages("src", exclude=["*.test"]),
    package_dir={"": "src"},
    python_requires=">=3.6",
    entry_points={
        "console_scripts": ["sys-line = sys_line.__main__:main"]
    },
    cmdclass={"clean": CleanCommand},
)
