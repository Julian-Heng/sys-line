#!/usr/bin/env python3

""" JSON utils """

import json


class SimpleNamespaceJsonEncoder(json.JSONEncoder):
    """ JSON Encoder for a SimpleNamespace object """

    def default(self, o):
        return o.__dict__


def json_pretty_string(json_string):
    """ Indents a json string """
    return json.dumps(json.loads(json_string), indent=4)
