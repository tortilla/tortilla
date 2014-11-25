# -*- coding: utf-8 -*-

import sys


_version = sys.version_info
is_py2 = (_version.major == 2)
is_py3 = (_version.major == 3)


if is_py2:
    string_type = basestring
    to_unicode = unicode
else:
    # we've made an assumption that `str` will still exist in future
    # Python versions
    string_type = str
    to_unicode = str
