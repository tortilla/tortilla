# -*- coding: utf-8 -*-


def run_from_ipython():
    try:
        __IPYTHON__
        return True
    except NameError:
        return False
