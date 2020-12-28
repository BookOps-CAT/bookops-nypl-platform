# -*- coding: utf-8 -*-

"""
bookops_nypl_platform.session testing
"""
from contextlib import contextmanager
import datetime
import os
import pytest

import requests

from bookops_nypl_platform import __title__, __version__

# from bookops_nypl_platform.authorize import PlatformToken
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
        err_msg = "Invalid authorization. Argument must be an instance of `PlatformToken` obj."
        with pytest.raises(BookopsPlatformError) as exc:
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
        err_msg = "Invalid `target` argument passed into a Platform session."
        with pytest.raises(BookopsPlatformError) as exc:
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
        err_msg = "Argument `agent` must be a string."
        with pytest.raises(BookopsPlatformError) as exc:
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

    def test_get_item_list_url(self, mock_token):
        with PlatformSession(authorization=mock_token) as session:
            assert (
                session._get_item_list_url()
                == "https://platform.nypl.org/api/v0.1/items"
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

    @pytest.mark.parametrize(
        "arg,expectation",
        [
            (12345678, "12345678"),
            (123456789, "12345678"),
            ("12345678", "12345678"),
            ("123456789", "12345678"),
            ("b12345678", "12345678"),
            ("b123456789", "12345678"),
            ("i21234567x", "21234567"),
            ("i21234567", "21234567"),
        ],
    )
    def test_prep_sierra_number(self, mock_token, arg, expectation):
        with PlatformSession(authorization=mock_token) as session:
            assert session._prep_sierra_number(arg) == expectation

    @pytest.mark.parametrize(
        "arg",
        [12345, 1234567890, "12345", "bl1234567", "a12345678"],
    )
    def test_prep_sierra_number_exceptions(self, mock_token, arg):
        err_msg = "Invalid Sierra number passed."
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError) as exc:
                session._prep_sierra_number(arg)
            assert err_msg in str(exc.value)

    @pytest.mark.parametrize(
        "arg,expectation",
        [
            ("12345678", "12345678"),
            ("12345678,12345679", "12345678,12345679"),
            ("b12345678a", "12345678"),
            ("b12345678a,b12345679a", "12345678,12345679"),
            ("12345678a,12345679a", "12345678,12345679"),
        ],
    )
    def test_prep_sierra_numbers(self, mock_token, arg, expectation):
        with PlatformSession(authorization=mock_token) as session:
            assert session._prep_sierra_numbers(arg) == expectation

    @pytest.mark.parametrize(
        "arg", ["12345", "bl1234569", "a123456789", "b12345", "1234567890"]
    )
    def test_prep_sierra_numbers_exceptions(self, mock_token, arg):
        err_msg = "Invalid Sierra number passed."
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError) as exc:
                session._prep_sierra_numbers(arg)
            assert err_msg in str(exc.value)

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
        err_msg = "Both arguments `id` and `nyplSource` are required."
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError) as exc:
                session.get_bib(arg_id, nyplSource=arg_src)
            assert err_msg in str(exc.value)

    def test_get_bib_with_invalid_id(self, mock_token):
        err_msg = "Invalid Sierra number passed."
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError) as exc:
                session.get_bib("bt1234567")
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
        err_msg = "Missing required positional argument."
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError) as exc:
                session.get_bib_list(id_arg, sn_arg, cn_arg)
            assert err_msg in str(exc.value)

    @pytest.mark.parametrize(
        "id_arg,sn_arg,cn_arg",
        [
            ("12345678", None, None),
            (None, "9781234567890", None),
            (None, None, "12345"),
        ],
    )
    def test_get_bib_list_correct_ids(
        self, mock_token, id_arg, sn_arg, cn_arg, mock_successful_session_get_response
    ):
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
        err_msg = "Both arguments `id` and `nyplSource` are required."
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError) as exc:
                session.get_bib_items(arg_id, nyplSource=arg_src)
            assert err_msg in str(exc.value)

    def test_get_bib_items_with_invalid_bibNo(self, mock_token):
        err_msg = "Invalid Sierra number passed."
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError) as exc:
                session.get_bib_items("a12345678")
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

    @pytest.mark.parametrize(
        "id_arg,ba_arg,bi_arg",
        [(None, None, None), ("", "", ""), ([], [], [])],
    )
    def test_get_item_list_arguments_errors(self, mock_token, id_arg, ba_arg, bi_arg):
        err_msg = "Missing required positional argument."
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError) as exc:
                session.get_item_list(id_arg, ba_arg, bi_arg)
            assert err_msg in str(exc.value)

    @pytest.mark.parametrize(
        "id_arg,ba_arg,bi_arg",
        [
            ("12345678", None, None),
            (None, "33333834590594", None),
            (None, None, "b198280646"),
        ],
    )
    def test_get_item_list_correct_ids(
        self, mock_token, id_arg, ba_arg, bi_arg, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            with does_not_raise():
                session.get_item_list(id_arg, ba_arg, bi_arg)

    def test_get_item_list_successful_request(
        self, mock_token, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            response = session.get_item_list(id=["i304400737,i304400750"])
            assert response.status_code == 200

    def test_get_item_list_with_stale_token(
        self, mock_token, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            assert session.authorization.is_expired() is False
            session.authorization.expires_on = (
                datetime.datetime.now() - datetime.timedelta(seconds=1)
            )
            assert session.authorization.is_expired() is True
            response = session.get_item_list(id="i304400737")
            assert response.status_code == 200
            assert session.authorization.is_expired() is False

    def test_get_item_list_BookopsPlatformError_exception(
        self, mock_token, mock_bookopsplatformerror
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_item_list(id="i304400737")

    def test_get_item_list_Timeout_exception(self, mock_token, mock_timeout):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_item_list(id="i304400737")

    def test_get_item_list_Connection_exception(self, mock_token, mock_connectionerror):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_item_list(id="i304400737")

    def test_get_item_list_unexpected_exception(
        self, mock_token, mock_unexpected_error
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.get_item_list(id="i304400737")

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
        err_msg = "Both arguments `id` and `nyplSource` are required."
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError) as exc:
                session.check_bib_is_research(arg_id, nyplSource=arg_src)
            assert err_msg in str(exc.value)

    def test_check_bib_is_research_with_invald_id(self, mock_token):
        err_msg = "Invalid Sierra number passed."
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError) as exc:
                session.check_bib_is_research("a12345678")
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

    @pytest.mark.parametrize(
        "arg",
        ["", [], None],
    )
    def test_search_standardNos_argument_errors(self, mock_token, arg):
        err_msg = "Missing required positional argument `keywords`."
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError) as exc:
                session.search_standardNos(arg)
            assert err_msg in str(exc.value)

    def test_search_standardNos_successful_request(
        self, mock_token, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            response = session.search_standardNos(keywords=[12345, 12346])
            assert response.status_code == 200

    def test_search_standardNos_with_stale_token(
        self, mock_token, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            assert session.authorization.is_expired() is False
            session.authorization.expires_on = (
                datetime.datetime.now() - datetime.timedelta(seconds=1)
            )
            assert session.authorization.is_expired() is True
            response = session.search_standardNos(keywords="12345678")
            assert response.status_code == 200
            assert session.authorization.is_expired() is False

    def test_search_standardNos_BookopsPlatformError_exception(
        self, mock_token, mock_bookopsplatformerror
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.search_standardNos(keywords="12345678")

    def test_search_standardNos_Timeout_exception(self, mock_token, mock_timeout):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.search_standardNos(keywords="12345678")

    def test_search_standardNos_Connection_exception(
        self, mock_token, mock_connectionerror
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.search_standardNos(keywords="12345678")

    def test_search_standardNos_unexpected_exception(
        self, mock_token, mock_unexpected_error
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.search_standardNos(keywords="12345678")

    @pytest.mark.parametrize(
        "arg",
        ["", [], None],
    )
    def test_search_controlNos_argument_errors(self, mock_token, arg):
        err_msg = "Missing required positional argument `keywords`."
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError) as exc:
                session.search_controlNos(arg)
            assert err_msg in str(exc.value)

    def test_search_controlNos_successful_request(
        self, mock_token, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            response = session.search_controlNos(keywords=[12345, 12346])
            assert response.status_code == 200

    def test_search_controlNos_with_stale_token(
        self, mock_token, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            assert session.authorization.is_expired() is False
            session.authorization.expires_on = (
                datetime.datetime.now() - datetime.timedelta(seconds=1)
            )
            assert session.authorization.is_expired() is True
            response = session.search_controlNos(keywords="12345678")
            assert response.status_code == 200
            assert session.authorization.is_expired() is False

    def test_search_controlNos_BookopsPlatformError_exception(
        self, mock_token, mock_bookopsplatformerror
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.search_controlNos(keywords="12345678")

    def test_search_controlNos_Timeout_exception(self, mock_token, mock_timeout):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.search_controlNos(keywords="12345678")

    def test_search_controlNos_Connection_exception(
        self, mock_token, mock_connectionerror
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.search_controlNos(keywords="12345678")

    def test_search_controlNos_unexpected_exception(
        self, mock_token, mock_unexpected_error
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.search_controlNos(keywords="12345678")

    @pytest.mark.parametrize(
        "arg",
        ["", [], None],
    )
    def test_search_bibNos_argument_missing(self, mock_token, arg):
        err_msg = "Missing required positional argument `keywords`."
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError) as exc:
                session.search_bibNos(arg)
            assert err_msg in str(exc.value)

    def test_search_bibNos_invalid_number(self, mock_token):
        err_msg = "Invalid Sierra number passed."
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError) as exc:
                session.search_bibNos("a12345678")
            assert err_msg in str(exc.value)

    def test_search_bibNos_successful_request(
        self, mock_token, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            response = session.search_bibNos(keywords=[12345678, 12345679])
            assert response.status_code == 200

    def test_search_bibNos_with_stale_token(
        self, mock_token, mock_successful_session_get_response
    ):
        with PlatformSession(authorization=mock_token) as session:
            assert session.authorization.is_expired() is False
            session.authorization.expires_on = (
                datetime.datetime.now() - datetime.timedelta(seconds=1)
            )
            assert session.authorization.is_expired() is True
            response = session.search_bibNos(keywords="12345678")
            assert response.status_code == 200
            assert session.authorization.is_expired() is False

    def test_search_bibNos_BookopsPlatformError_exception(
        self, mock_token, mock_bookopsplatformerror
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.search_bibNos(keywords="12345678")

    def test_search_bibNos_Timeout_exception(self, mock_token, mock_timeout):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.search_bibNos(keywords="12345678")

    def test_search_bibNos_Connection_exception(self, mock_token, mock_connectionerror):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.search_bibNos(keywords="12345678")

    def test_search_bibNos_unexpected_exception(
        self, mock_token, mock_unexpected_error
    ):
        with PlatformSession(authorization=mock_token) as session:
            with pytest.raises(BookopsPlatformError):
                session.search_bibNos(keywords="12345678")


@pytest.mark.webtest
class TestLivePlatform:
    """ Runs rudimentary tests against live NYPL Platform endpoints"""

    def test_get_bib(self, live_token, response_top_keys, bib_data_keys):
        """Tests get_bib method"""
        agent = os.getenv("NPagent")
        agent = f"{agent}/testing"
        with PlatformSession(authorization=live_token, agent=agent) as session:
            response = session.get_bib(id=21790265)

            assert response.status_code == 200
            assert (
                response.url
                == "https://platform.nypl.org/api/v0.1/bibs/sierra-nypl/21790265"
            )
            assert response.request.headers["User-Agent"] == agent
            assert response.request.headers["Accept"] == "application/json"
            assert sorted(response.json().keys()) == response_top_keys
            assert sorted(response.json()["data"].keys()) == bib_data_keys

    def test_get_bib_list(self, live_token, response_top_keys, bib_data_keys):

        agent = os.getenv("NPagent")
        agent = f"{agent}/testing"
        with PlatformSession(authorization=live_token, agent=agent) as session:
            response = session.get_bib_list(id=["b21790265a", "b21721339a"], limit=15)

            assert response.status_code == 200
            assert (
                response.url
                == "https://platform.nypl.org/api/v0.1/bibs?id=21790265%2C21721339&nyplSource=sierra-nypl&deleted=False&limit=15&offset=0"
            )
            assert sorted(response.json().keys()) == response_top_keys
            assert response.json()["count"] == 2
            assert sorted(response.json()["data"][0].keys()) == bib_data_keys

    def test_get_bib_items(self, live_token, response_top_keys, bib_items_keys):
        agent = os.getenv("NPagent")
        agent = f"{agent}/testing"
        with PlatformSession(authorization=live_token, agent=agent) as session:
            response = session.get_bib_items(id="b21790265a")

            assert response.status_code == 200
            assert (
                response.url
                == "https://platform.nypl.org/api/v0.1/bibs/sierra-nypl/21790265/items"
            )
            assert sorted(response.json().keys()) == response_top_keys
            assert response.json()["count"] == 1
            assert sorted(response.json()["data"][0].keys()) == bib_items_keys

    def test_get_item_list(self, live_token, response_top_keys):
        agent = os.getenv("NPagent")
        agent = f"{agent}/testing"
        with PlatformSession(authorization=live_token, agent=agent) as session:
            response = session.get_item_list(id="i372231731")

            assert response.status_code == 200
            assert (
                response.url
                == "https://platform.nypl.org/api/v0.1/items?id=37223173&nyplSource=sierra-nypl&deleted=False&limit=10&offset=0"
            )
            assert sorted(response.json().keys()) == response_top_keys

    def test_check_bib_is_research(self, live_token):
        agent = os.getenv("NPagent")
        agent = f"{agent}/testing"
        with PlatformSession(authorization=live_token, agent=agent) as session:
            response = session.check_bib_is_research(id="b21790265a")

            assert response.status_code == 200
            assert (
                response.url
                == "https://platform.nypl.org/api/v0.1/bibs/sierra-nypl/21790265/is-research"
            )
            assert sorted(response.json().keys()) == sorted(
                ["nyplSource", "id", "isResearch"]
            )

    def test_search_standardNos(self, live_token):
        agent = os.getenv("NPagent")
        agent = f"{agent}/testing"
        with PlatformSession(authorization=live_token, agent=agent) as session:
            response = session.search_standardNos(
                keywords=["9780316230032", "0674976002"], limit=12
            )

            assert response.status_code == 200
            assert (
                response.url
                == "https://platform.nypl.org/api/v0.1/bibs?standardNumber=9780316230032%2C0674976002&nyplSource=sierra-nypl&deleted=False&limit=12&offset=0"
            )

    def test_search_controlNos(self, live_token):
        agent = os.getenv("NPagent")
        agent = f"{agent}/testing"
        with PlatformSession(authorization=live_token, agent=agent) as session:
            response = session.search_controlNos(
                keywords=["1089804986", "1006480637"], limit=1, offset=1
            )
        assert response.status_code == 200
        assert (
            response.url
            == "https://platform.nypl.org/api/v0.1/bibs?controlNumber=1089804986%2C1006480637&nyplSource=sierra-nypl&deleted=False&limit=1&offset=1"
        )

    def test_search_bibNos(self, live_token):
        agent = os.getenv("NPagent")
        agent = f"{agent}/testing"
        with PlatformSession(authorization=live_token, agent=agent) as session:
            response = session.search_bibNos(
                keywords=[21790265, 21721339], limit=1, offset=1
            )
        assert response.status_code == 200
        assert (
            response.url
            == "https://platform.nypl.org/api/v0.1/bibs?id=21790265%2C21721339&nyplSource=sierra-nypl&deleted=False&limit=1&offset=1"
        )
