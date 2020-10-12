# -*- coding: utf-8 -*-

"""
bookops_nypl_platform.session testing
"""
from contextlib import contextmanager
import datetime
import pytest

import requests

from bookops_nypl_platform import __title__, __version__
from bookops_nypl_platform.errors import BookopsPlatformError
from bookops_nypl_platform.session import PlatformSession


@contextmanager
def does_not_raise():
    yield


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

    def test_fetch_new_token(self, mock_token):
        with PlatformSession(authorization=mock_token) as session:
            assert session.authorization.is_expired() is False
            # force stale token
            session.authorization.expires_on = (
                datetime.datetime.now() - datetime.timedelta(seconds=1)
            )
            # verify token is expired
            assert session.authorization.is_expired() is True

            # fetch new one and retests
            session._fetch_new_token()
            assert session.authorization.is_expired() is False

    def test_fetch_new_token_exceptions(self, mock_token, mock_timeout):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session._fetch_new_token()

    @pytest.mark.parametrize("arg", ["12345678", 12345678])
    def test_get_bib_url_production(self, mock_token, arg):
        with PlatformSession(authorization=mock_token) as session:
            assert (
                session._get_bib_url(arg, "sierra-nypl")
                == "https://platform.nypl.org/api/v0.1/bibs/sierra-nypl/12345678"
            )

    def test_get_bib_url_development(self, mock_token):
        with PlatformSession(authorization=mock_token, target="dev") as session:
            assert (
                session._get_bib_url("1234567", "sierra-nypl")
                == "https://dev-platform.nypl.org/api/v0.1/bibs/sierra-nypl/1234567"
            )

    def test_get_bib_list_url(self, mock_token):
        with PlatformSession(authorization=mock_token) as session:
            assert (
                session._get_bib_list_url() == "https://platform.nypl.org/api/v0.1/bibs"
            )

    def test_get_bib_items_url(self, mock_token):
        with PlatformSession(authorization=mock_token) as session:
            assert (
                session._get_bib_items_url(1234567, "sierra-nypl")
                == "https://platform.nypl.org/api/v0.1/bibs/sierra-nypl/1234567/items"
            )

    def test_get_bib_is_reasearch(self, mock_token):
        with PlatformSession(authorization=mock_token) as session:
            assert (
                session._check_bib_is_research_url("1234567", "sierra-nypl")
                == "https://platform.nypl.org/api/v0.1/bibs/sierra-nypl/1234567/is-research"
            )

    @pytest.mark.parametrize(
        "arg,expectation",
        [
            (None, None),
            ("", None),
            ([], None),
            ("12345", "12345"),
            (12345, "12345"),
            (["12345"], "12345"),
            ([12345], "12345"),
            ([12345, 12346], "12345,12346"),
            (["12345", "12346"], "12345,12346"),
            ("12345,12346", "12345,12346"),
        ],
    )
    def test_prep_multi_keywords(self, mock_token, arg, expectation):
        with PlatformSession(authorization=mock_token) as session:
            assert session._prep_multi_keywords(arg) == expectation

    def test_get_bib_success(self, mock_token, mock_successful_session_get_response):
        with PlatformSession(authorization=mock_token) as session:
            response = session.get_bib("12345678")
            assert response.status_code == 200

    @pytest.mark.parametrize(
        "arg_id, arg_src",
        [
            ("", None),
            ("", "sierra-nypl"),
            ("123456", ""),
            (None, None),
            ("123456", None),
        ],
    )
    def test_get_bib_without_id(self, mock_token, arg_id, arg_src):
        with PlatformSession(authorization=mock_token) as session:
            err_msg = "Required argument `id` is missing."
            with pytest.raises(BookopsPlatformError) as exc:
                session.get_bib(arg_id, nyplSource=arg_src)
                assert err_msg in str(exc.value)

    def test_get_bib_with_stale_token(
        self, mock_token, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            assert session.authorization.is_expired() is False
            session.authorization.expires_on = (
                datetime.datetime.now() - datetime.timedelta(seconds=1)
            )
            assert session.authorization.is_expired() is True
            response = session.get_bib("12345678")
            assert response.status_code == 200
            assert session.authorization.is_expired() is False

    def test_get_bib_BookopsPlatformError_exception(
        self, mock_token, mock_bookopsplatformerror
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_bib("12345678")

    def test_get_bib_Timeout_exception(self, mock_token, mock_timeout):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_bib("12345678")

    def test_get_bib_Connection_exception(self, mock_token, mock_connectionerror):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_bib("12345678")

    def test_get_bib_unexpected_exception(self, mock_token, mock_unexpected_error):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_bib("12345678")

    @pytest.mark.parametrize(
        "id_arg,sn_arg,cn_arg",
        [(None, None, None), ("", "", ""), ([], [], [])],
    )
    def test_get_bib_list_arguments_errors(self, mock_token, id_arg, sn_arg, cn_arg):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError) as exc:
                session.get_bib_list(id_arg, sn_arg, cn_arg)
                err_msg = "Missing required positional argument."
                assert err_msg in str(exc.value)

    @pytest.mark.parametrize(
        "id_arg,sn_arg,cn_arg",
        [
            ("12345678", None, None),
            (None, "9781234567890", None),
            (None, None, "12345"),
        ],
    )
    def test_get_bib_list_correct_ids(self, mock_token, id_arg, sn_arg, cn_arg):
        with PlatformSession(authorization=mock_token) as session:
            with does_not_raise():
                session.get_bib_list(id_arg, sn_arg, cn_arg)

    def test_get_bib_list_successful_request(
        self, mock_token, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            response = session.get_bib_list(standardNumber=[12345, 12346])
            assert response.status_code == 200

    def test_get_bib_list_with_stale_token(
        self, mock_token, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            assert session.authorization.is_expired() is False
            session.authorization.expires_on = (
                datetime.datetime.now() - datetime.timedelta(seconds=1)
            )
            assert session.authorization.is_expired() is True
            response = session.get_bib_list(id="12345678")
            assert response.status_code == 200
            assert session.authorization.is_expired() is False

    def test_get_bib_list_BookopsPlatformError_exception(
        self, mock_token, mock_bookopsplatformerror
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_bib_list(id="12345678")

    def test_get_bib_list_Timeout_exception(self, mock_token, mock_timeout):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_bib_list(id="12345678")

    def test_get_bib_list_Connection_exception(self, mock_token, mock_connectionerror):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_bib_list(id="12345678")

    def test_get_bib_list_unexpected_exception(self, mock_token, mock_unexpected_error):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_bib_list(id="12345678")

    def test_get_bib_items_success(
        self, mock_token, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            response = session.get_bib_items("12345678")
            assert response.status_code == 200

    @pytest.mark.parametrize(
        "arg_id,arg_src",
        [
            ("", None),
            ("", "sierra-nypl"),
            ("123456", ""),
            (None, None),
            ("123456", None),
        ],
    )
    def test_get_bib_items_without_id(self, mock_token, arg_id, arg_src):
        with PlatformSession(authorization=mock_token) as session:
            err_msg = "Required argument `id` is missing."
            with pytest.raises(BookopsPlatformError) as exc:
                session.get_bib_items(arg_id, nyplSource=arg_src)
                assert err_msg in str(exc.value)

    def test_get_bib_items_with_stale_token(
        self, mock_token, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            assert session.authorization.is_expired() is False
            session.authorization.expires_on = (
                datetime.datetime.now() - datetime.timedelta(seconds=1)
            )
            assert session.authorization.is_expired() is True
            response = session.get_bib_items("12345678")
            assert response.status_code == 200
            assert session.authorization.is_expired() is False

    def test_get_bib_items_BookopsPlatformError_exception(
        self, mock_token, mock_bookopsplatformerror
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_bib_items("12345678")

    def test_get_bib_itmes_Timeout_exception(self, mock_token, mock_timeout):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_bib_items("12345678")

    def test_get_bib_items_Connection_exception(self, mock_token, mock_connectionerror):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_bib_items("12345678")

    def test_get_bib_items_unexpected_exception(
        self, mock_token, mock_unexpected_error
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_bib_items("12345678")

    def test_check_bib_is_research_success(
        self, mock_token, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            response = session.check_bib_is_research("12345678")
            assert response.status_code == 200

    @pytest.mark.parametrize(
        "arg_id,arg_src",
        [
            ("", None),
            ("", "sierra-nypl"),
            ("123456", ""),
            (None, None),
            ("123456", None),
        ],
    )
    def test_check_bib_is_research_without_id(self, mock_token, arg_id, arg_src):
        with PlatformSession(authorization=mock_token) as session:
            err_msg = "Required argument `id` is missing."
            with pytest.raises(BookopsPlatformError) as exc:
                session.check_bib_is_research(arg_id, nyplSource=arg_src)
                assert err_msg in str(exc.value)

    def test_check_bib_is_research_with_stale_token(
        self, mock_token, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            assert session.authorization.is_expired() is False
            session.authorization.expires_on = (
                datetime.datetime.now() - datetime.timedelta(seconds=1)
            )
            assert session.authorization.is_expired() is True
            response = session.check_bib_is_research("12345678")
            assert response.status_code == 200
            assert session.authorization.is_expired() is False

    def test_check_bib_is_research_BookopsPlatformError_exception(
        self, mock_token, mock_bookopsplatformerror
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.check_bib_is_research("12345678")

    def test_check_bib_is_research_Timeout_exception(self, mock_token, mock_timeout):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.check_bib_is_research("12345678")

    def test_check_bib_is_research_Connection_exception(
        self, mock_token, mock_connectionerror
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.check_bib_is_research("12345678")

    def test_check_bib_is_research_unexpected_exception(
        self, mock_token, mock_unexpected_error
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.check_bib_is_research("12345678")
