# -*- coding: utf-8 -*-

from . import wrappers


def wrap(url, debug=False):
    """Syntax sugar for creating service wrappers."""
    return wrappers.Service(url, debug)
