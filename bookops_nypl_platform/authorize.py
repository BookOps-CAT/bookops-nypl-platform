# -*- coding: utf-8 -*-

"""
bookops_nypl_platform.authorize
===============================
This module provides method to authenicate subsequent requests to NYPL Platform
by obtaining an access token used for authorization.
"""
import datetime
import sys
from typing import Any, Dict, Optional, Tuple, Union

import requests


from . import __title__, __version__
from .errors import BookopsPlatformError


class PlatformToken:
    """
    Authenticates access to NYPL Platform API and returns an access token.
    Supports only client_credential flow.

    Args:
        client_id:      client id
        client_secret:  client secret
        oauth_server:   NYPL OAuth Server
        agent:          "User-Agent" parameter to be passed in the request
                        header
        timeout:        how long to wait for server to respond before
                        giving up; default value is 3 seconds

    Example:


    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        oauth_server: str,
        agent: Optional[str] = None,
        timeout: Union[int, float, Tuple[int, int], Tuple[float, float], None] = (
            3,
            3,
        ),
    ):
        """Constructor"""

        for value in (client_id, client_secret, oauth_server):
            if not value:
                raise BookopsPlatformError("Missing Platform authentication argument.")

        self.token_str = None
        self.expires_on = None
        self.server_response = None
        self.auth = (client_id, client_secret)
        self.oauth_server = oauth_server
        self.timeout = timeout

        if agent is None:
            self.agent = f"{__title__}/{__version__}"
        else:
            self.agent = agent

        # make access token request
        self._get_token()

    def _token_url(self) -> str:
        return f"{self.oauth_server}/oauth/token"

    def _parse_access_token_string(self, server_response: Dict[str, Any]) -> str:
        """
        Parsers access token string from auth_server response

        Args:
            server_response:    oauth_server response in dict format

        Returns:
            access_token
        """
        try:
            return server_response["access_token"]
        except (KeyError, TypeError):
            raise BookopsPlatformError(
                "Missing access_token parameter in the oauth_server response."
            )

    def _calculate_expiration_time(
        self, server_response: Dict[str, Any]
    ) -> datetime.datetime:
        """
        Calculates access token expiration time based on it's life lenght
        indicated in oauth_server response

        Args:
            server_resopnse:    oauth_server response in dict format

        Returns:
            expires_on:         datetime object
        """
        try:
            expires_on = datetime.datetime.now() + datetime.timedelta(
                seconds=server_response["expires_in"] - 1
            )
            return expires_on
        except (KeyError, TypeError):
            raise BookopsPlatformError(
                "Missing expires_in parameter in the oauth_server response."
            )

    def _get_token(self):
        """
        Fetches NYPL Platform access token
        """
        token_url = self._token_url()
        header = {"User-Agent": self.agent}
        data = {"grant_type": "client_credentials"}

        try:
            response = requests.post(
                token_url,
                auth=self.auth,
                headers=header,
                data=data,
                timeout=self.timeout,
            )
            if response.status_code == requests.codes.ok:
                self.server_response = response
                self.token_str = self._parse_access_token_string(response.json())
                self.expires_on = self._calculate_expiration_time(response.json())
            else:
                raise BookopsPlatformError(
                    f"Invalid request. Oauth server retruned error: {response.json()}"
                )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            raise BookopsPlatformError(f"Trouble connecting: {sys.exc_info()[0]}")
        except BookopsPlatformError:
            raise
        except Exception:
            raise BookopsPlatformError(f"Unexpected error occured: {sys.exc_info()[0]}")

    def is_expired(self):
        """
        Checks if token is expired

        Returns:
            Boolean

        Example:
        >>> token.is_expired()
        False

        """
        if self.expires_on < datetime.datetime.now():
            return True
        else:
            return False

    def __repr__(self):
        return (
            f"<token: {self.token_str}, "
            f"expires_on: {self.expires_on:%Y-%m-%d %H:%M:%S}, "
            f"server_response: {self.server_response.json()}>"
        )
