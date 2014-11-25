# -*- coding: utf-8 -*-

from . import wrappers


def wrap(url, debug=False, cache_lifetime=None):
    """Syntax sugar for creating service wrappers."""
    return wrappers.Wrap(part=url, debug=debug, cache_lifetime=cache_lifetime)
