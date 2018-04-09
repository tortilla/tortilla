# -*- coding: utf-8 -*-


def hyphenate(path):
    """Replaces underscores with hyphens"""
    return path.replace('_', '-')


def mixedcase(path):
    """Removes underscores and capitalizes the neighbouring character"""
    words = path.split('_')
    return words[0] + ''.join(word.title() for word in words[1:])


def camelcase(path):
    """Applies mixedcase and capitalizes the first character"""
    return mixedcase('_{0}'.format(path))
