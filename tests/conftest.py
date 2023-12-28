# -*- coding: utf-8 -*-

import datetime
import os
import json

import pytest
import requests


from bookops_nypl_platform import PlatformToken
from bookops_nypl_platform.errors import BookopsPlatformError


class FakeDate(datetime.datetime):
    @classmethod
    def now(cls):
        return cls(2019, 1, 1, 17, 0, 0)


class MockUnexpectedException:
    def __init__(self, *args, **kwargs):
        raise Exception


class MockTimeout:
    def __init__(self, *args, **kwargs):
        raise requests.exceptions.Timeout


class MockConnectionError:
    def __init__(self, *args, **kwargs):
        raise requests.exceptions.ConnectionError


class MockBookopsPlatformError:
    def __init__(self, *args, **kwargs):
        raise BookopsPlatformError


class MockAuthServerResponseSuccess:
    """Simulates oauth server response to successful token request"""

    def __init__(self):
        self.status_code = 200

    def json(self):
        return {
            "access_token": "token_string_here",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": "scopes_here",
            "id_token": "token_string_here",
        }


class MockSuccessfulHTTP200SessionResponse:
    def __init__(self):
        self.status_code = 200


class MockAuthServerResponseFailure:
    """Simulates oauth server response to successful token request"""

    def __init__(self):
        self.status_code = 400

    def json(self):
        return {"error": "No grant_type specified", "error_description": None}


@pytest.fixture
def mock_successful_post_token_response(monkeypatch):
    def mock_oauth_server_response(*args, **kwargs):
        return MockAuthServerResponseSuccess()

    monkeypatch.setattr(requests, "post", mock_oauth_server_response)


@pytest.fixture
def mock_failed_post_token_response(monkeypatch):
    def mock_oauth_server_response(*args, **kwargs):
        return MockAuthServerResponseFailure()

    monkeypatch.setattr(requests, "post", mock_oauth_server_response)


@pytest.fixture
def mock_successful_session_get_response(monkeypatch):
    def mock_api_response(*args, **kwargs):
        return MockSuccessfulHTTP200SessionResponse()

    monkeypatch.setattr(requests.Session, "get", mock_api_response)


@pytest.fixture
def mock_token(mock_successful_post_token_response):
    return PlatformToken("my_client", "my_secret", "oauth_url")


@pytest.fixture
def mock_unexpected_error(monkeypatch):
    monkeypatch.setattr("requests.post", MockUnexpectedException)
    monkeypatch.setattr("requests.Session.get", MockUnexpectedException)


@pytest.fixture
def mock_timeout(monkeypatch):
    monkeypatch.setattr("requests.post", MockTimeout)
    monkeypatch.setattr("requests.Session.get", MockTimeout)


@pytest.fixture
def mock_connectionerror(monkeypatch):
    monkeypatch.setattr("requests.post", MockConnectionError)
    monkeypatch.setattr("requests.Session.get", MockConnectionError)


@pytest.fixture
def mock_bookopsplatformerror(monkeypatch):
    monkeypatch.setattr("requests.Session.get", MockBookopsPlatformError)


@pytest.fixture
def mock_datetime_now(monkeypatch):
    monkeypatch.setattr(datetime, "datetime", FakeDate)


@pytest.fixture
def live_keys():
    if os.name == "nt":
        fh = os.path.join(
            os.environ["USERPROFILE"], ".cred/.platform/tomasz_platform.json"
        )
        with open(fh, "r") as file:
            data = json.load(file)
            os.environ["NP_CLIENT_ID"] = data["client-id"]
            os.environ["NP_CLIENT_SECRET"] = data["client-secret"]
            os.environ["NP_OAUTH_SERVER"] = data["oauth-server"]
            os.environ["NP_AGENT"] = data["agent"]

    else:
        # Github Actions env variables defined in the repository settings
        pass


@pytest.fixture
def live_token(live_keys):
    token = PlatformToken(
        client_id=os.getenv("NP_CLIENT_ID"),
        client_secret=os.getenv("NP_CLIENT_SECRET"),
        oauth_server=os.getenv("NP_OAUTH_SERVER"),
        agent=os.getenv("NP_AGENT"),
    )
    return token


@pytest.fixture
def response_top_keys():
    return sorted(["data", "count", "totalCount", "statusCode", "debugInfo"])


@pytest.fixture
def bib_data_keys():
    return sorted(
        [
            "id",
            "nyplSource",
            "nyplType",
            "updatedDate",
            "createdDate",
            "deletedDate",
            "deleted",
            "locations",
            "suppressed",
            "lang",
            "title",
            "author",
            "materialType",
            "bibLevel",
            "publishYear",
            "catalogDate",
            "country",
            "normTitle",
            "normAuthor",
            "standardNumbers",
            "controlNumber",
            "fixedFields",
            "varFields",
        ]
    )


@pytest.fixture
def bib_items_keys():
    return sorted(
        [
            "nyplSource",
            "bibIds",
            "id",
            "nyplType",
            "updatedDate",
            "createdDate",
            "deletedDate",
            "deleted",
            "location",
            "status",
            "barcode",
            "callNumber",
            "itemType",
            "fixedFields",
            "varFields",
        ]
    )
