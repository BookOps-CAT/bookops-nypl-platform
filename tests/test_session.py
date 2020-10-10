# -*- coding: utf-8 -*-

"""
bookops_nypl_platform.session testing
"""

import pytest

from bookops_nypl_platform import __title__, __version__
from bookops_nypl_platform.errors import BookopsPlatformError
from bookops_nypl_platform.session import PlatformSession


class TestPlatformSession:
    """
    Test of the PlatformSession
    """

    def test_authorization_invalid_argument(self):
        with pytest.raises(BookopsPlatformError) as exc:
            err_msg = "Invalid authorization. Argument must be an instance of `PlatformToken` obj."
            PlatformSession("my_token")
            assert err_msg in str(exc.value)

    @pytest.mark.parametrize(
        "arg,expectation",
        [
            ("prod", "https://platform.nypl.org/api/v0.1"),
            ("dev", "https://dev-platform.nypl.org/api/v0.1"),
        ],
    )
    def test_target_argument(self, arg, expectation, mock_token):
        assert (
            PlatformSession(authorization=mock_token, target=arg).base_url
            == expectation
        )

    def test_target_argument_exception(self, mock_token):
        with pytest.raises(BookopsPlatformError) as exc:
            err_msg = "Invalid `target` argument passed into a Platform session."
            PlatformSession(authorization=mock_token, target=None)
            assert err_msg in str(exc.value)

    def test_default_base_url_parameter(self, mock_token):
        assert (
            PlatformSession(authorization=mock_token).base_url
            == "https://platform.nypl.org/api/v0.1"
        )

    def test_default_agent_parameter(self, mock_token):
        with PlatformSession(authorization=mock_token) as session:
            assert session.headers["User-Agent"] == f"{__title__}/{__version__}"

    def test_custom_agent_argument(self, mock_token):
        with PlatformSession(authorization=mock_token, agent="my_app") as session:
            assert session.headers["User-Agent"] == "my_app"

    def test_invalid_agent_argument_exception(self, mock_token):
        with pytest.raises(BookopsPlatformError) as exc:
            err_msg = "Argument `agent` must be a string."
            PlatformSession(authorization=mock_token, agent=1234)
            assert err_msg in str(exc.value)

    def test_default_timeout_parameter(self, mock_token):
        with PlatformSession(authorization=mock_token) as session:
            assert session.timeout == (3, 3)

    def test_custom_timeout_parameter(self, mock_token):
        with PlatformSession(authorization=mock_token, timeout=1.5) as session:
            assert session.timeout == 1.5
