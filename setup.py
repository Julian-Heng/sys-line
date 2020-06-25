#!/usr/bin/env python3

from pathlib import Path
import setuptools


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

        pattern = ("build", "dist", "*.pyc", "*.tgz", "src/*.egg-info")
        files = []

        for i in pattern:
            find_files(".", i, files)

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
    author="Julian Heng",
    author_email="julianhengwl@gmail.com",
    description="a simple status line generator",
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": ["sys-line = sys_line.__main__:main"]
    },
    cmdclass={"clean": CleanCommand}
)
