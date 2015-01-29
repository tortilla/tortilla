# -*- coding: utf-8 -*-

from formats import FormatBank, discover_json, discover_yaml


formats = FormatBank()

discover_json(formats, content_type='application/json')
discover_yaml(formats, content_type='application/x-yaml')


def run_from_ipython():
    try:
        __IPYTHON__
        return True
    except NameError:
        return False
