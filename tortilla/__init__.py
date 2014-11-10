# -*- coding: utf-8 -*-

"""
    Tortilla
    ~~~~~~~~

    A tiny Python library for creating wrappers around external APIs.

    Usage::

        >>> import tortilla
        >>> github = tortilla.wrap('https://api.github.com')
        >>> users = github('/users')
        >>> redodo = users.get('redodo')
        >>> redodo.id
        2227416

    :copyright: (c) 2014 by Hidde Bultsma.
    :license: MIT, see LICENSE for more details.
"""

from . import utils
from .api import wrap
from .wrappers import Service, Endpoint
