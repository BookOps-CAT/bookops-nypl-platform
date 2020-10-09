# -*- coding: utf-8 -*-

import datetime

# import json

import pytest
import requests


from bookops_nypl_platform import PlatformToken


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
def mock_token(mock_successful_post_token_response):
    return PlatformToken("my_client", "my_secret", "oauth_url")


@pytest.fixture
def mock_unexpected_error(monkeypatch):
    monkeypatch.setattr("requests.post", MockUnexpectedException)


@pytest.fixture
def mock_timeout(monkeypatch):
    monkeypatch.setattr("requests.post", MockTimeout)


@pytest.fixture
def mock_connectionerror(monkeypatch):
    monkeypatch.setattr("requests.post", MockConnectionError)


@pytest.fixture
def mock_datetime_now(monkeypatch):
    monkeypatch.setattr(datetime, "datetime", FakeDate)
