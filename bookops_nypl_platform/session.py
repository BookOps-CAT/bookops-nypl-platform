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

    def _check_bib_is_research_url(self, id: Union[str, int], nyplSource: str) -> str:
        return f"{self.base_url}/bibs/{nyplSource}/{id}/is-research"

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

    def _get_bib_url(self, id: Union[str, int], nyplSource: str) -> str:
        return f"{self.base_url}/bibs/{nyplSource}/{id}"

    def _get_bib_list_url(self) -> str:
        return f"{self.base_url}/bibs"

    def _get_bib_items_url(self, id: Union[str, int], nyplSource: str) -> str:
        return f"{self.base_url}/bibs/{nyplSource}/{id}/items"

    def _prep_multi_keywords(
        self, keywords: Union[str, List[str], List[int]]
    ) -> List[str]:
        """
        Verifies or converts passed keywords into a comma separated string.

        Args:
            keywords:       a comma separated string of keywords or a list
                            of strings or integers

        Returns:
            keywords:       a comma separated string of keywords
        """
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

    def _prep_sierra_number(self, bid: Union[str, int]) -> str:
        """
        Verifies and converts Sierra bib numbers

        Args:
            bid:            Sierra bib number as string or int

        Returns:
            bid
        """
        err_msg = "Invalid Sierra bib number passed."

        if type(bid) is int:
            bid = str(bid)

        if "b" in bid.lower():
            bid = bid[1:]
        if len(bid) == 8:
            if not bid.isdigit():
                raise BookopsPlatformError(err_msg)
        elif len(bid) == 9:
            bid = bid[:8]
            if not bid.isdigit():
                raise BookopsPlatformError(err_msg)
        else:
            raise BookopsPlatformError(err_msg)

        return bid

    def _prep_sierra_numbers(self, bibNos: str) -> str:
        """
        Verifies or conversts passed Sierra bib numbers into a comma separated string.

        Args:
            bibNos:         a comma separated string of Sierra bib numbers

        Returns:
            verified_nos:   a comma separated string of Sierrra bib numbers
        """
        verified_nos = []

        for bid in bibNos.split(","):
            bid = self._prep_sierra_number(bid)
            verified_nos.append(bid)

        return ",".join(verified_nos)

    def _update_authorization(self):
        """
        Updates Bearer token in PlatformSession headers
        """
        self.headers.update({"Authorization": f"Bearer {self.authorization.token_str}"})

    def get_bib(
        self, id: Union[str, int], nyplSource: str = "sierra-nypl", hooks=None
    ) -> Type[requests.Response]:
        """
        Requests a specific resource using its id number.

        Args:
            id:             resource id; for Sierra bibliographic
                            records that means Sierra bib number with or without
                            'b' prefix and 9th digit check

            nyplSource:     data source; default 'sierra-nypl'; required
            hooks:          Requests library hook system that can be
                            used for signal event handling, see more at:
                            https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

        Returns:
            `requests.Response` object
        """
        if not all([id, nyplSource]):
            raise BookopsPlatformError(
                "Both arguments `id` and `nyplSource` are required."
            )

        # verify id
        id = self._prep_sierra_number(id)

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
        nyplSource: str = "sierra-nypl",
        deleted: bool = False,
        createdDate: str = None,
        updatedDate: str = None,
        limit: int = 10,
        offset: int = 0,
        hooks: Dict = None,
    ) -> Type[requests.Response]:
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
                            separated string or a list of strings
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

        Returns:
            `requests.Response` object

        """

        # format any search keywords:
        id = self._prep_multi_keywords(id)
        standardNumber = self._prep_multi_keywords(standardNumber)
        controlNumber = self._prep_multi_keywords(controlNumber)

        if not any([id, standardNumber, controlNumber]):
            raise BookopsPlatformError("Missing required positional argument.")

        # additionally verify Sierra bib numbers
        if id:
            id = self._prep_sierra_numbers(id)

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
            response = self.get(url, params=payload, timeout=self.timeout, hooks=hooks)
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            raise BookopsPlatformError(f"Connection error: {sys.exc_info()[0]}")
        except BookopsPlatformError:
            raise
        except Exception:
            raise BookopsPlatformError(f"Unexpected request error: {sys.exc_info()[0]}")

    def get_bib_items(
        self, id: Union[str, int], nyplSource: str = "sierra-nypl", hooks: Dict = None
    ) -> Type[requests.Response]:
        """
        Retrieves items linked to a specified bib

        Args:
            id:             resource id; for Sierra bibliographic
                            records that means Sierra bib number without
                            the 'b' prefix and without the last check digit
                            example: '21790265'

            nyplSource:     data source; default 'sierra-nypl'; required
            hooks:          Requests library hook system that can be
                            used for signal event handling, see more at:
                            https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

        Returns:
            `requests.Response` object
        """

        if not all([id, nyplSource]):
            raise BookopsPlatformError(
                "Both arguments `id` and `nyplSource` are required."
            )

        # verify id
        id = self._prep_sierra_number(id)

        url = self._get_bib_items_url(id, nyplSource)

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

    def check_bib_is_research(
        self, id: Union[str, int], nyplSource: str = "sierra-nypl", hooks: Dict = None
    ) -> Type[requests.Response]:
        """
        Checks if bib is a reaserch libraries bib

        Args:
            id:             resource id; for Sierra bibliographic
                            records that means Sierra bib number without
                            the 'b' prefix and without the last check digit
                            example: '21790265'

            nyplSource:     data source; default 'sierra-nypl'; required
            hooks:          Requests library hook system that can be
                            used for signal event handling, see more at:
                            https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

        Returns:
            `requests.Response` object
        """
        if not all([id, nyplSource]):
            raise BookopsPlatformError(
                "Both arguments `id` and `nyplSource` are required."
            )

        # verify id
        id = self._prep_sierra_number(id)

        url = self._check_bib_is_research_url(id, nyplSource)

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

    def search_standardNos(
        self,
        keywords: Union[str, List[str]],
        deleted: bool = False,
        limit: int = 10,
        offset: int = 0,
        hooks: Dict = None,
    ) -> Type[requests.Response]:
        """
        Makes a request for bibs with matching standard numbers (ISBNs or UPCs) from the
        020 or 024 MARC tag.

        Args:
            keywords:       list of standard numbers such as ISBNs or UPCs (020 and
                            024 MARC tags); can be a comma separated string or a
                            list of strings
            deleted:        True or False
            limit:          number of records to retrieve per request
            offset:         starting number of results page
            hooks:          Requests library hook system that can be
                            used for signal event handling, see more at:
                            https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

        Returns:
            `requests.Response` object

        """

        keywords = self._prep_multi_keywords(keywords)

        if not keywords:
            raise BookopsPlatformError(
                "Missing required positional argument `keywords`."
            )

        url = self._get_bib_list_url()
        payload = {
            "standardNumber": keywords,
            "nyplSource": "sierra-nypl",
            "deleted": deleted,
            "limit": limit,
            "offset": offset,
        }

        # check if token expired and request new one if needed
        if self.authorization.is_expired():
            self._fetch_new_token()

        # send request
        try:
            response = self.get(url, params=payload, timeout=self.timeout, hooks=hooks)
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            raise BookopsPlatformError(f"Connection error: {sys.exc_info()[0]}")
        except BookopsPlatformError:
            raise
        except Exception:
            raise BookopsPlatformError(f"Unexpected request error: {sys.exc_info()[0]}")

    def search_controlNos(
        self,
        keywords: Union[str, List[str]],
        deleted: bool = False,
        limit: int = 10,
        offset: int = 0,
        hooks: Dict = None,
    ) -> Type[requests.Response]:
        """
        Makes a request for bibs with matching control numbers from the 001 MARC tag.

        Args:
            keywords:       list of control numbers (001 MARC tag);
                            can be a comma separated string or a list of strings
            deleted:        True or False
            limit:          number of records to retrieve per request
            offset:         starting number of results page
            hooks:          Requests library hook system that can be
                            used for signal event handling, see more at:
                            https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

        Returns:
            `requests.Response` object

        """

        keywords = self._prep_multi_keywords(keywords)

        if not keywords:
            raise BookopsPlatformError(
                "Missing required positional argument `keywords`."
            )

        url = self._get_bib_list_url()
        payload = {
            "controlNumber": keywords,
            "nyplSource": "sierra-nypl",
            "deleted": deleted,
            "limit": limit,
            "offset": offset,
        }

        # check if token expired and request new one if needed
        if self.authorization.is_expired():
            self._fetch_new_token()

        # send request
        try:
            response = self.get(url, params=payload, timeout=self.timeout, hooks=hooks)
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            raise BookopsPlatformError(f"Connection error: {sys.exc_info()[0]}")
        except BookopsPlatformError:
            raise
        except Exception:
            raise BookopsPlatformError(f"Unexpected request error: {sys.exc_info()[0]}")

    def search_bibNos(
        self,
        keywords: Union[str, List[str], List[int]],
        deleted: bool = False,
        limit: int = 10,
        offset: int = 0,
        hooks: Dict = None,
    ) -> Type[requests.Response]:
        """
        Makes a request for resources with matching Sierra bib numbers.

        Args:
            keywords:       list of Sierra bib numbers;
                            can be a comma separated string or a list of strings or
                            integers;
                            bib numbers can be a string of 8 digits, or can include
                            the 'b' prefix and last, 9th digit check
            deleted:        True or False
            limit:          number of records to retrieve per request
            offset:         starting number of results page
            hooks:          Requests library hook system that can be
                            used for signal event handling, see more at:
                            https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

        Returns:
            `requests.Response` object

        """

        # prep Sierra bib numbers
        keywords = self._prep_multi_keywords(keywords)

        if not keywords:
            raise BookopsPlatformError(
                "Missing required positional argument `keywords`."
            )

        keywords = self._prep_sierra_numbers(keywords)

        # prep request
        url = self._get_bib_list_url()
        payload = {
            "id": keywords,
            "nyplSource": "sierra-nypl",
            "deleted": deleted,
            "limit": limit,
            "offset": offset,
        }

        # check if token expired and request new one if needed
        if self.authorization.is_expired():
            self._fetch_new_token()

        # send request
        try:
            response = self.get(url, params=payload, timeout=self.timeout, hooks=hooks)
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            raise BookopsPlatformError(f"Connection error: {sys.exc_info()[0]}")
        except BookopsPlatformError:
            raise
        except Exception:
            raise BookopsPlatformError(f"Unexpected request error: {sys.exc_info()[0]}")
