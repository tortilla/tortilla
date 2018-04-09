# -*- coding: utf-8 -*-

import six

from formats import FormatBank, discover_json, discover_yaml


formats = FormatBank()

discover_json(formats, content_type='application/json')
discover_yaml(formats, content_type='application/x-yaml')


def run_from_ipython():
    return getattr(__builtins__, "__IPYTHON__", False)


class Bunch(dict):
    def __init__(self, kwargs=None):
        if kwargs is None:
            kwargs = {}
        for key, value in six.iteritems(kwargs):
            kwargs[key] = bunchify(value)
        super(Bunch, self).__init__(kwargs)
        self.__dict__ = self


def bunchify(obj):
    if isinstance(obj, (list, tuple)):
        return [bunchify(item) for item in obj]
    if isinstance(obj, dict):
        return Bunch(obj)
    return obj
