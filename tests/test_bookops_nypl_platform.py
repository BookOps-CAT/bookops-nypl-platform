from bookops_nypl_platform import __title__, __version__


def test_version():
    assert __version__ == "0.5.0"


def test_title():
    assert __title__ == "bookops-nypl-platform"


def test_PlatfromToken_top_level_import():
    pass


def test_PlatformSession_top_level_import():
    pass


def test_BookopsPlatformError_top_level_import():
    pass
