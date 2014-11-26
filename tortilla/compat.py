# -*- coding: utf-8 -*-

import sys


_version = sys.version_info
is_py2 = (_version[0] == 2)
is_py3 = (_version[0] == 3)


if is_py2:
    string_type = basestring
else:
    # we've made an assumption that `str` will still exist in future
    # Python versions
    string_type = str
