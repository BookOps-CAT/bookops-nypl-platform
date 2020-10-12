# -*- coding: utf-8 -*-

"""
bookops_nypl_platform.session
=============================
This module provides a session functionality used for making requests
to NYPL Platform API
"""

import sys
from typing import Dict, List, Tuple, Type, Union

import requests

from . import __title__, __version__
from .authorize import PlatformToken
from .errors import BookopsPlatformError


class PlatformSession(requests.Session):
    """
    Opens a session with NYPL Platform API and provides methods
    to send requests to it.

    Args:
        authorization:                  authorization in form of the `PlatformToken` instance
        target:                 production ('prod') or development ('dev')
                                environment; default production
        agent:                  "User-agent" parameter to be passed in the request
                                header; usage strongly encouraged
        timeout:                how long to wait for server to send data before
                                giving up; default value is 3 seconds

    """

    def __init__(
        self,
        authorization: Type[PlatformToken],
        target: str = "prod",
        agent: str = None,
        timeout: Union[int, float, Tuple[int, int], Tuple[float, float]] = None,
    ):
        requests.Session.__init__(self)

        self.authorization = authorization
        if type(self.authorization).__name__ != "PlatformToken":
            raise BookopsPlatformError(
                "Invalid authorization. Argument must be an instance of `PlatformToken` obj."
            )

        # determine base url
        if target == "prod":
            self.base_url = "https://platform.nypl.org/api/v0.1"
        elif target == "dev":
            self.base_url = "https://dev-platform.nypl.org/api/v0.1"
        else:
            raise BookopsPlatformError(
                "Invalid `target` argument passed into a Platform session."
            )

        # set agent for requests
        if agent is None:
            self.headers.update({"User-Agent": f"{__title__}/{__version__}"})
        elif type(agent) is str:
            self.headers.update({"User-Agent": agent})
        else:
            raise BookopsPlatformError("Argument `agent` must be a string.")

        # set timout
        self.timeout = timeout
        if self.timeout is None:
            self.timeout = (3, 3)

        # set session wide response content type
        self.headers.update({"Accept": "application/json"})

        # set token bearer for the session
        self._update_authorization()

    def _update_authorization(self):
        self.headers.update({"Authorization": f"Bearer {self.authorization.token_str}"})

    def _fetch_new_token(self):
        """
        Requests new access token from the oauth server and updates
        session headers with new Authorization
        """
        try:
            self.authorization._get_token()
            self._update_authorization()
        except BookopsPlatformError:
            raise

    def _get_bib_url(self, id, nyplSource):
        return f"{self.base_url}/bibs/{nyplSource}/{id}"

    def _get_bib_list_url(self):
        return f"{self.base_url}/bibs"

    def _prep_multi_keywords(self, keywords):
        if type(keywords) is str:
            keywords = keywords.strip()
        elif type(keywords) is int:
            keywords = str(keywords)
        elif type(keywords) is list:
            keywords = ",".join([str(k) for k in keywords])

        if not keywords:
            return None
        else:
            return keywords

    def get_bib(self, id: str, nyplSource: str = "sierra-nypl", hooks=None):
        """
        Requests a specific resource using its id number.

        Args:
            id:             resource id; for Sierra bibliographic
                            records that means Sierra bib number without
                            the 'b' prefix and without the last check digit
                            example: '21790265'

            nyplSource:     data source; default 'sierra-nypl'
            hooks:          Requests library hook system that can be
                            used for signal event handling, see more at:
                            https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

        Returns:
            `requests.Response` object
        """
        if not id:
            raise BookopsPlatformError("Required argument `id` is missing.")

        url = self._get_bib_url(id, nyplSource)

        # check if token expired and request new one if needed
        if self.authorization.is_expired():
            self._fetch_new_token()

        # send request
        try:
            response = self.get(url, timeout=self.timeout, hooks=hooks)
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            raise BookopsPlatformError(f"Connection error: {sys.exc_info()[0]}")
        except BookopsPlatformError:
            raise
        except Exception:
            raise BookopsPlatformError(f"Unexpected request error: {sys.exc_info()[0]}")

    def get_bib_list(
        self,
        id: Union[str, List[str], List[int]] = None,
        standardNumber: Union[str, List[str]] = None,
        controlNumber: Union[str, List[str]] = None,
        nyplSource: str = "nypl-sierra",
        deleted: bool = False,
        createdDate: str = None,
        updatedDate: str = None,
        limit: int = 10,
        offset: int = 1,
        hooks: Dict = None,
    ):
        """
        Retrieve multiple resources using a variety of indexes, for example:
        Sierra bib #s, standard numbers & control numbers

        Args:
            id:             list of resource ids; can be a comma separated string
                            or list of strings
            standardNumber: list of standard numbers such as ISBNs or UPCs (020 & 024
                            MARC tags); can be a comma separated string or a list of
                            strings
            controlNumber:  list of MARC control numbers (001 MARC tag); can be a comma
                            seperated string or a list of strings
            nyplSource:     data source; default 'sierra-nypl'
            deleted:        True or False
            createdDate:    specific start date or date range as a string, example:
                            [2013-09-03T13:17:45Z,2013-09-03T13:37:45Z]
            updatedDate:    specific start date or date range as a string, example:
                            [2013-09-03T13:17:45Z,2013-09-03T13:37:45Z]
            limit:          number of records to retrieve per request
            offset:         starting number of results page
            hooks:          Requests library hook system that can be
                            used for signal event handling, see more at:
                            https://requests.readthedocs.io/en/master/user/advanced/#event-hooks


        """

        # format argument accordingly:
        id = self._prep_multi_keywords(id)
        standardNumber = self._prep_multi_keywords(standardNumber)
        controlNumber = self._prep_multi_keywords(controlNumber)

        if not any([id, standardNumber, controlNumber]):
            raise BookopsPlatformError("Missing required positional argument.")

        url = self._get_bib_list_url()
        payload = {
            "id": id,
            "standardNumber": standardNumber,
            "controlNumber": controlNumber,
            "nyplSource": nyplSource,
            "deleted": deleted,
            "createdDate": createdDate,
            "updatedDate": updatedDate,
            "limit": limit,
            "offset": offset,
        }

        # check if token expired and request new one if needed
        if self.authorization.is_expired():
            self._fetch_new_token()

        # send request
        try:
            response = self.get(url, timeout=self.timeout, hooks=hooks)
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            raise BookopsPlatformError(f"Connection error: {sys.exc_info()[0]}")
        except BookopsPlatformError:
            raise
        except Exception:
            raise BookopsPlatformError(f"Unexpected request error: {sys.exc_info()[0]}")

    def get_bib_items(self):
        pass

    def check_bib_is_research(self):
        pass

    def search_standardNos(
        self,
        standardNos: Union[str, List[str], List[int]],
        deleted: bool = False,
        limit: int = 10,
        offset: int = 1,
    ):
        pass

    def search_controlNos(
        self,
        controlNos: Union[str, List[str], List[int]],
        deleted: bool = False,
        limit: int = 10,
        offset: int = 1,
    ):
        pass

    def search_bidNos(
        bibNos: Union[str, List[str], List[int]],
        deleted: bool = False,
        limit: int = 10,
        offset: int = 1,
    ):
        pass
