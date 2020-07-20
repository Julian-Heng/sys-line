#!/usr/bin/env python3
# pylint: disable=invalid-name

""" sys-line initialization """

import sys

from .systems.abstract import System
from .tools.cli import parse_cli
from .tools.format import FormatTree


def main():
    """ Main method """
    options = parse_cli(sys.argv[1:])
    system = System.create_instance(options)

    if system is not None:
        if options.all is not None:
            domains = options.all if options.all else system.SHORT_DOMAINS
            for domain in domains:
                print(getattr(system, domain))
        elif options.format:
            for fmt in options.format:
                print(FormatTree(system, fmt).build())
    else:
        sys.exit(2)
