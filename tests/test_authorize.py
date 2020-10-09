# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

import pytest


from bookops_nypl_platform.authorize import PlatformToken
from bookops_nypl_platform.errors import BookopsPlatformError


class TestPlatformToken:
    """
    Test PlatfromToken class
    """

    @pytest.mark.parametrize(
        "args, msg",
        [
            ((None, None, None), "Missing Platform authentication argument."),
            (("key", None, None), "Missing Platform authentication argument."),
            ((None, "secret", None), "Missing Platform authentication argument."),
            ((None, None, "server"), "Missing Platform authentication argument."),
            (("", "", ""), "Missing Platform authentication argument."),
            (("key", "", ""), "Missing Platform authentication argument."),
            (("", "secret", ""), "Missing Platform authentication argument."),
            (("", "", "server"), "Missing Platform authentication argument."),
        ],
    )
    def test_missing_init_arguments(self, args, msg):
        with pytest.raises(BookopsPlatformError) as exc:
            PlatformToken(*args)
            assert msg in str(exc.value)

    def test_auth(self, mock_successful_post_token_response):
        token = PlatformToken("my_client_id", "my_client_secret", "oauth_url")
        assert token.auth == ("my_client_id", "my_client_secret")

    def test_oauth_server(self, mock_successful_post_token_response):
        token = PlatformToken("my_client_id", "my_client_secret", "oauth_url")
        assert token.oauth_server == "oauth_url"

    def test_default_agent(self, mock_successful_post_token_response):
        from bookops_nypl_platform import __title__, __version__

        token = PlatformToken("my_client_id", "my_client_secret", "oauth_url")
        assert token.agent == f"{__title__}/{__version__}"

    def test_deafault_timeout(self, mock_successful_post_token_response):
        token = PlatformToken("my_client_id", "my_client_secret", "oauth_url")
        assert token.timeout == (3, 3)

    def test_custom_agent(self, mock_successful_post_token_response):
        token = PlatformToken(
            "my_client_id", "my_client_secret", "oauth_url", agent="my_client/1.0"
        )
        assert token.agent == "my_client/1.0"

    def test_custom_timeout(self, mock_successful_post_token_response):
        token = PlatformToken(
            "my_client_id", "my_client_secret", "oauth_url", timeout=1.5
        )
        assert token.timeout == 1.5

    def test_token_url(self, mock_successful_post_token_response):
        token = PlatformToken("my_client_id", "my_client_secret", "oauth_url")
        assert token._token_url() == "oauth_url/oauth/token"

    def test_header(self, mock_successful_post_token_response):
        token = PlatformToken(
            "my_client_id", "my_client_secret", "oauth_url", agent="my_client/1.0"
        )
        assert token._header() == {"User-Agent": "my_client/1.0"}

    def test_parse_access_token_string_sucess(self, mock_token):
        token = mock_token
        res = {
            "access_token": "token_string_here",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": "scopes_here",
            "id_token": "token_string_here",
        }

        assert token._parse_access_token_string(res) == "token_string_here"

    @pytest.mark.parametrize(
        "arg,expectation",
        [
            (None, pytest.raises(BookopsPlatformError)),
            ({"a": 1}, pytest.raises(BookopsPlatformError)),
            ("some_str", pytest.raises(BookopsPlatformError)),
        ],
    )
    def test_parse_access_token_string_failure(self, mock_token, arg, expectation):
        token = mock_token
        err_msg = "Missing access_token parameter in the oauth_server response."
        with expectation as exc:
            token._parse_access_token_string(arg)
            assert err_msg in str(exc.value)

    def test_calculate_expiration_time_success(self, mock_token):
        token = mock_token
        res = {"expires_in": 3600}
        assert token._calculate_expiration_time(res) == datetime.now() + timedelta(
            seconds=3599
        )

    @pytest.mark.parametrize(
        "arg,expectation",
        [
            (None, pytest.raises(BookopsPlatformError)),
            ("", pytest.raises(BookopsPlatformError)),
            ({}, pytest.raises(BookopsPlatformError)),
        ],
    )
    def test_calculate_expiration_time_failure(self, mock_token, arg, expectation):
        token = mock_token
        err_msg = "Missing expires_in parameter in the oauth_server response."
        with expectation as exc:
            token._calculate_expiration_time(arg)
            assert err_msg in str(exc.value)

    def test_get_token_timeout(self, mock_timeout):
        with pytest.raises(BookopsPlatformError):
            PlatformToken("my_client_id", "my_client_secret", "oauth_url")

    def test_get_token_connectionerror(self, mock_connectionerror):
        with pytest.raises(BookopsPlatformError):
            PlatformToken("my_client_id", "my_client_secret", "oauth_url")

    def test_get_token_unexpectederror(self, mock_unexpected_error):
        with pytest.raises(BookopsPlatformError):
            PlatformToken("my_client_id", "my_client_secret", "oauth_url")

    def test_get_token_http_400_error(self, mock_failed_post_token_response):
        with pytest.raises(BookopsPlatformError):
            PlatformToken("my_client_id", "my_client_secret", "oauth_url")

    def test_get_token_success(self, mock_successful_post_token_response):
        token = PlatformToken("my_client_id", "my_client_secret", "oauth_url")
        res = {
            "access_token": "token_string_here",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": "scopes_here",
            "id_token": "token_string_here",
        }
        assert token.token_request_response == res
        assert token.token_str == "token_string_here"
        assert token.expires_on == datetime.now() + timedelta(seconds=3599)

    def test_is_expired_False(self, mock_token):
        token = mock_token
        assert token.is_expired() is False

    def test_is_expired_True(self, mock_token):
        token = mock_token
        token.expires_on = datetime.now() - timedelta(seconds=1)
        assert token.is_expired() is True

    def test_printing_token(self, mock_token):
        token = mock_token
        expires_on = datetime.now() + timedelta(seconds=3599)
        assert (
            str(token)
            == f"<token: token_string_here, expires_on: {expires_on}, token_request_response: {{'access_token': 'token_string_here', 'expires_in': 3600, 'token_type': 'Bearer', 'scope': 'scopes_here', 'id_token': 'token_string_here'}}>"
        )
