# -*- coding: utf-8 -*-

"""
bookops_nypl_platform.session
=============================
This module provides a session functionality used for making requests
to NYPL Platform API
"""

import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import requests

from . import __title__, __version__
from .authorize import PlatformToken
from .errors import BookopsPlatformError


class PlatformSession(requests.Session):
    """
    Opens a session with NYPL Platform API and provides methods
    to send requests to it.

    Args:
        authorization:          authorization in form of the `PlatformToken` instance
        target:                 production ('prod') or development ('dev')
                                environment; default production
        agent:                  "User-agent" parameter to be passed in the request
                                header; usage strongly encouraged
        timeout:                how long to wait for server to send data before
                                giving up; default value is 3 seconds
    Example:

    >>> from bookops_nypl_platform import PlatformSession
    >>> with PlatformSession(authorization=token, agent="my_client") as session:
            response = session.search_standardNos(
                keywords=["9780316230032", "0674976002"])
            print(response.json())
    """

    def __init__(
        self,
        authorization: PlatformToken,
        target: str = "prod",
        agent: Optional[str] = None,
        timeout: Union[int, float, Tuple[int, int], Tuple[float, float], None] = (
            3,
            3,
        ),
    ):
        requests.Session.__init__(self)

        self.authorization = authorization
        if not isinstance(self.authorization, PlatformToken):
            raise BookopsPlatformError(
                "Invalid authorization. Argument must be an instance of "
                "`PlatformToken` obj."
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
        elif isinstance(agent, str):
            self.headers.update({"User-Agent": agent})
        else:
            raise BookopsPlatformError("Argument `agent` must be a string.")

        # set timeout
        self.timeout = timeout

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

    def _get_item_list_url(self) -> str:
        return f"{self.base_url}/items"

    def _prep_multi_keywords(
        self, keywords: Union[str, List[str], List[int], None]
    ) -> Optional[str]:
        """
        Verifies or converts passed keywords into a comma separated string.

        Args:
            keywords:       a comma separated string of keywords or a list
                            of strings or integers

        Returns:
            keywords:       a comma separated string of keywords
        """
        if isinstance(keywords, str):
            keywords = keywords.strip()
        elif isinstance(keywords, int):
            keywords = str(keywords)
        elif isinstance(keywords, list):
            keywords = ",".join([str(k) for k in keywords])
        if not keywords:
            return None
        return keywords

    def _prep_sierra_number(self, sid: Union[str, int]) -> str:
        """
        Verifies and formats Sierra bib numbers

        Args:
            sid:            Sierra bib or item number as string or int

        Returns:
            sid
        """
        err_msg = "Invalid Sierra number passed."

        if isinstance(sid, int):
            sid = str(sid)

        if sid.lower()[0] in ("b", "i"):
            sid = sid[1:]
        if len(sid) == 8:
            if not sid.isdigit():
                raise BookopsPlatformError(err_msg)
        elif len(sid) == 9:
            sid = sid[:8]
            if not sid.isdigit():
                raise BookopsPlatformError(err_msg)
        else:
            raise BookopsPlatformError(err_msg)

        return sid

    def _prep_sierra_numbers(self, sids: str) -> str:
        """
        Verifies or conversts passed Sierra bib numbers into a comma separated string.

        Args:
            sids:           a comma separated string of Sierra bib numbers

        Returns:
            verified_nos:   a comma separated string of Sierrra bib numbers
        """
        verified_nos = []

        for bid in sids.split(","):
            bid = self._prep_sierra_number(bid)
            verified_nos.append(bid)

        return ",".join(verified_nos)

    def _update_authorization(self):
        """
        Updates Bearer token in PlatformSession headers
        """
        self.headers.update({"Authorization": f"Bearer {self.authorization.token_str}"})

    def get_bib(
        self,
        id: Union[str, int],
        nyplSource: str = "sierra-nypl",
        hooks: Optional[Dict[str, Callable]] = None,
    ) -> requests.Response:
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
        id: Union[str, List[str], List[int], None] = None,
        standardNumber: Union[str, List[str], None] = None,
        controlNumber: Union[str, List[str], None] = None,
        nyplSource: str = "sierra-nypl",
        deleted: bool = False,
        createdDate: Optional[str] = None,
        updatedDate: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        hooks: Optional[Dict[str, Callable]] = None,
    ) -> requests.Response:
        """
        Retrieve multiple bib resources using a variety of indexes, for example:
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
        payload: Dict[str, Any] = {
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
        self,
        id: Union[str, int],
        nyplSource: str = "sierra-nypl",
        hooks: Optional[Dict[str, Callable]] = None,
    ) -> requests.Response:
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

    def get_item_list(
        self,
        id: Union[str, List[str], List[int], None] = None,
        barcode: Optional[str] = None,
        bibId: Union[str, int, None] = None,
        nyplSource: str = "sierra-nypl",
        deleted: bool = False,
        createdDate: Optional[str] = None,
        updatedDate: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        hooks: Optional[Dict[str, Callable]] = None,
    ) -> requests.Response:
        """
        Retrieve multiple item resources using a variety of indexes, for example:
        Sierra item numbers, barcodes, bib number.

        Args:
            id:             list of item record ids; can be a comma separated string
                            or list of strings
            barcode:        barcode string
            bibId:          Sierra bib number
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

        if not any([id, barcode, bibId]):
            raise BookopsPlatformError("Missing required positional argument.")

        if id:
            id = self._prep_sierra_numbers(id)

        # additionally verify Sierra bib numbers
        if bibId:
            bibId = self._prep_sierra_number(bibId)

        url = self._get_item_list_url()
        payload: Dict[str, Any] = {
            "id": id,
            "barcode": barcode,
            "bibId": bibId,
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

    def check_bib_is_research(
        self,
        id: Union[str, int],
        nyplSource: str = "sierra-nypl",
        hooks: Optional[Dict[str, Callable]] = None,
    ) -> requests.Response:
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
        hooks: Optional[Dict[str, Callable]] = None,
    ) -> requests.Response:
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

        standardNumbers = self._prep_multi_keywords(keywords)

        if not keywords:
            raise BookopsPlatformError(
                "Missing required positional argument `keywords`."
            )

        url = self._get_bib_list_url()
        payload: Dict[str, Any] = {
            "standardNumber": standardNumbers,
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
        hooks: Optional[Dict[str, Callable]] = None,
    ) -> requests.Response:
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

        controlNumbers = self._prep_multi_keywords(keywords)

        if not keywords:
            raise BookopsPlatformError(
                "Missing required positional argument `keywords`."
            )

        url = self._get_bib_list_url()
        payload: Dict[str, Any] = {
            "controlNumber": controlNumbers,
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
        hooks: Optional[Dict[str, Callable]] = None,
    ) -> requests.Response:
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
        prepped_keywords = self._prep_multi_keywords(keywords)

        if not prepped_keywords:
            raise BookopsPlatformError(
                "Missing required positional argument `keywords`."
            )

        ids = self._prep_sierra_numbers(prepped_keywords)

        # prep request
        url = self._get_bib_list_url()
        payload: Dict[str, Any] = {
            "id": ids,
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
