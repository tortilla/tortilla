# -*- coding: utf-8 -*-

from . import wrappers


def wrap(url, **options):
    """Syntax sugar for creating service wrappers."""
    return wrappers.Wrap(part=url, **options)
