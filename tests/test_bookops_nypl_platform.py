# -*- coding: utf-8 -*-

from bookops_nypl_platform import __version__, __title__


def test_version():
    assert __version__ == "0.1.0"


def test_title():
    assert __title__ == "bookops-nypl-platform"


def test_PlatfromToken_top_level_import():
    from bookops_nypl_platform import PlatformToken
