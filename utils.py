# -*- coding: utf-8 -*-

import six


class Bunch(object):
    """Recursive implementation of the Bunch pattern."""
    def __init__(self, **kwargs):
        for key, value in six.iteritems(kwargs):
            if isinstance(value, dict):
                self.__dict__[key] = Bunch(**value)
            else:
                self.__dict__[key] = value
