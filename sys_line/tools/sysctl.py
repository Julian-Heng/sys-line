#!/usr/bin/env python3

from .utils import run


class Sysctl():

    def __init__(self):
        self.sysctl = run(["sysctl", "-A"]).strip().split("\n")
        self.sysctl = dict(i.split(":", 1) for i in self.sysctl if i)


    def query(self, key):
        try:
            return self.sysctl[key]
        except KeyError:
            return None
