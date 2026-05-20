"""
bookops_nypl_platform.session
=============================
This module provides a session functionality used for making requests
to NYPL Platform API
"""

import sys
from typing import Any, Callable, Optional, Union

import requests

from . import __title__, __version__
from .authorize import PlatformToken
from .errors import BookopsPlatformError


class PlatformSession(requests.Session):
    """
    Opens a session with NYPL Platform API and provides methods
    to send requests to it.

    Args:
        authorization:
            authorization token in form of the `PlatformToken` instance
        target:
            whether session should query the production ('prod') or development ('dev')
            environment; default is `prod`
        agent:
            "User-agent" parameter to be passed in the request header;
            usage is strongly encouraged
        timeout:
            how long to wait for server to send data before giving up;
            default value is 3 seconds
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
        timeout: Union[int, float, tuple[int, int], tuple[float, float], None] = (3, 3),
    ) -> None:
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

    def _fetch_new_token(self) -> None:
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

    def _get_hold_requests_url(self) -> str:
        return f"{self.base_url}/hold-requests"

    def _get_hold_requests_by_id_url(self, id: Union[str, int]) -> str:
        return f"{self.base_url}/hold-requests/{id}"

    def _get_item_list_url(self) -> str:
        return f"{self.base_url}/items"

    def _prep_multi_keywords(
        self, keywords: Union[str, int, list[str], list[int], None]
    ) -> Optional[str]:
        """
        Verifies or converts passed keywords into a comma separated string.

        Args:
            keywords:
                a comma separated string of keywords or a list of strings
                and/or integers.

        Returns:
            keywords as a comma separated string
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
        Verifies and formats Sierra bib numbers.

        Args:
            sid:
                Sierra bib or item number as string or int

        Returns:
            Sierra bib or item ID as a string
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
        Verifies or converts Sierra bib numbers into a comma separated string.

        Args:
            sids:
                a comma separated string of Sierra bib numbers

        Returns:
            a comma separated string of Sierra bib numbers in proper format
        """
        verified_nos = []

        for bid in sids.split(","):
            bid = self._prep_sierra_number(bid)
            verified_nos.append(bid)

        return ",".join(verified_nos)

    def _update_authorization(self) -> None:
        """Updates Bearer token in `PlatformSession` headers"""
        self.headers.update({"Authorization": f"Bearer {self.authorization.token_str}"})

    def get_bib(
        self,
        id: Union[str, int],
        nyplSource: str = "sierra-nypl",
        hooks: Optional[dict[str, Callable]] = None,
    ) -> requests.Response:
        """
        Requests a specific bib record resource using its Sierra bib ID.

        Uses GET /bibs/{nyplSource}/{id} endpoint.

        Args:
            id:
                Sierra bib number with or without 'b' prefix and 9th digit check
            nyplSource:
                data source; default is 'sierra-nypl'
            hooks:
                Requests library hook system that can be used for signal event handling,
                see more at: https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

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
        id: Union[str, list[str], list[int], None] = None,
        standardNumber: Union[str, list[str], None] = None,
        controlNumber: Union[str, list[str], None] = None,
        nyplSource: str = "sierra-nypl",
        deleted: bool = False,
        createdDate: Optional[str] = None,
        updatedDate: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        hooks: Optional[dict[str, Callable]] = None,
    ) -> requests.Response:
        """
        Retrieve multiple bib resources using a variety of indexes.
        Available indexes include Sierra bib IDs, standard numbers & control numbers.

        Uses GET /bibs endpoint.

        Args:
            id:
                a list of sierra bib IDs as a comma separated string or list of strings
            standardNumber:
                a list of standard numbers such as ISBNs or UPCs (020 & 024 MARC tags)
                as a comma separated string or a list of strings
            controlNumber:
                a list of MARC control numbers (001 MARC tag) as a comma separated
                string or a list of strings
            nyplSource:
                data source; default is 'sierra-nypl'
            deleted:
                whether or not the record has been deleted as a bool
            createdDate:
                when the record was created as a string. May be a single date or date
                range.

                Example:
                    [2013-09-03T13:17:45Z,2013-09-03T13:37:45Z]
            updatedDate:
                when the record was last updated as a string. May be a single date or
                date range.

                Example:
                    [2013-09-03T13:17:45Z,2013-09-03T13:37:45Z]
            limit:
                how many records to return. default is 10.
            offset:
                first record to return from results page. default is 0.
            hooks:
                Requests library hook system that can be used for signal event handling,
                see more at: https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

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
        payload: dict[str, Any] = {
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
        hooks: Optional[dict[str, Callable]] = None,
    ) -> requests.Response:
        """
        Retrieves items linked to a specified bib.

        Uses GET /bibs/{nyplSource}/{id}/items endpoint.

        Args:
            id:
                Sierra bib number with or without 'b' prefix and 9th digit check
            nyplSource:
                data source; default is 'sierra-nypl'
            hooks:
                Requests library hook system that can be used for signal event handling,
                see more at: https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

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
        id: Union[str, int, list[str], list[int], None] = None,
        barcode: Union[str, int, list[str], list[int], None] = None,
        bibId: Union[str, int, None] = None,
        nyplSource: str = "sierra-nypl",
        deleted: bool = False,
        createdDate: Optional[str] = None,
        updatedDate: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        hooks: Optional[dict[str, Callable]] = None,
    ) -> requests.Response:
        """
        Retrieve multiple item resources using a variety of indexes.
        Available indexes include Sierra item IDs, barcodes & bib IDs.

        Uses GET /items endpoint.

        Args:
            id:
                a list of sierra item IDs as a comma separated string or list of strings
                and/or integers
            barcode:
                a list of barcodes as a comma separated string or list of strings
                and/or integers
            bibId:
                sierra bib ID as a string or integer
            nyplSource:
                data source; default is 'sierra-nypl'
            deleted:
                whether or not the record has been deleted as a bool
            createdDate:
                when the record was created as a string. May be a single date or date
                range.

                Example:
                    [2013-09-03T13:17:45Z,2013-09-03T13:37:45Z]
            updatedDate:
                when the record was last updated as a string. May be a single date or
                date range.

                Example:
                    [2013-09-03T13:17:45Z,2013-09-03T13:37:45Z]
            limit:
                how many records to return. default is 10.
            offset:
                first record to return from results page. default is 0.
            hooks:
                Requests library hook system that can be used for signal event handling,
                see more at: https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

        Returns:
            `requests.Response` object
        """

        # format any search keywords:
        id = self._prep_multi_keywords(id)

        if not any([id, barcode, bibId]):
            raise BookopsPlatformError("Missing required positional argument.")

        # verify Sierra item IDs
        if id:
            id = self._prep_sierra_numbers(id)

        # additionally verify Sierra bib numbers
        if bibId:
            bibId = self._prep_sierra_number(bibId)

        # format any barcodes
        if barcode:
            barcode = self._prep_multi_keywords(barcode)

        url = self._get_item_list_url()
        payload: dict[str, Any] = {
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
        hooks: Optional[dict[str, Callable]] = None,
    ) -> requests.Response:
        """
        Checks if a bib record is a research libraries bib.

        Uses GET /bibs/{nyplSource}/{id}/is-research endpoint.

        Args:
            id:
                Sierra bib number with or without 'b' prefix and 9th digit check.
                May be a string or integer
            nyplSource:
                data source; default is 'sierra-nypl'
            hooks:
                Requests library hook system that can be used for signal event handling,
                see more at: https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

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

    def get_hold_requests(
        self,
        patron: Optional[str] = None,
        record: Optional[str] = None,
        hooks: Optional[dict[str, Callable]] = None,
    ) -> requests.Response:
        """
        Get hold requests for a patron.

        Args:
            patron:
                Sierra patron ID as a string.
            nyplSource:
                data source; default is 'sierra-nypl'
            hooks:
                Requests library hook system that can be used for signal event handling,
                see more at: https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

        Returns:
            `requests.Response` object
        """
        url = self._get_hold_requests_url()
        # check if token expired and request new one if needed
        if self.authorization.is_expired():
            self._fetch_new_token()

        payload = {}
        if record:
            payload["record"] = record
        if patron:
            payload["patron"] = patron
        if not payload:
            raise ValueError("Request must contain record ID and/or patron ID.")
        # send request
        try:
            response = self.get(url, params=payload, timeout=self.timeout, hooks=hooks)
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            raise BookopsPlatformError(f"Connection error: {sys.exc_info()}")
        except BookopsPlatformError:
            raise
        except Exception:
            raise BookopsPlatformError(f"Unexpected request error: {sys.exc_info()[0]}")

    def get_hold_requests_by_id(
        self, id: str, hooks: Optional[dict[str, Callable]] = None
    ) -> requests.Response:
        """
        Get hold request record by hold request ID.

        Uses GET /hold-requests endpoint.

        Args:
            id:
                Hold request ID as a string.
            hooks:
                Requests library hook system that can be used for signal event handling,
                see more at: https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

        Returns:
            `requests.Response` object
        """
        url = self._get_hold_requests_by_id_url(id=id)
        # check if token expired and request new one if needed
        if self.authorization.is_expired():
            self._fetch_new_token()

        # send request
        try:
            response = self.get(url, timeout=self.timeout, hooks=hooks)
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            raise BookopsPlatformError(f"Connection error: {sys.exc_info()}")
        except BookopsPlatformError:
            raise
        except Exception:
            raise BookopsPlatformError(f"Unexpected request error: {sys.exc_info()[0]}")

    def search_standardNos(
        self,
        keywords: Union[str, list[str]],
        deleted: bool = False,
        limit: int = 10,
        offset: int = 0,
        hooks: Optional[dict[str, Callable]] = None,
    ) -> requests.Response:
        """
        Makes a request for bibs with matching standard numbers (ISBNs or UPCs) from the
        020 or 024 MARC tag.

        Uses GET /bibs endpoint and `standardNumber` query parameter.

        Args:
            keywords:
                a list of standard numbers such as ISBNs or UPCs (020 & 024 MARC tags)
                as a comma separated string or a list of strings
            deleted:
                whether or not the record has been deleted as a bool
            limit:
                how many records to return. default is 10.
            offset:
                first record to return from results page. default is 0.
            hooks:
                Requests library hook system that can be used for signal event handling,
                see more at: https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

        Returns:
            `requests.Response` object

        """

        standardNumbers = self._prep_multi_keywords(keywords)

        if not keywords:
            raise BookopsPlatformError(
                "Missing required positional argument `keywords`."
            )

        url = self._get_bib_list_url()
        payload: dict[str, Any] = {
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
        keywords: Union[str, list[str]],
        deleted: bool = False,
        limit: int = 10,
        offset: int = 0,
        hooks: Optional[dict[str, Callable]] = None,
    ) -> requests.Response:
        """
        Makes a request for bibs with matching control numbers from the 001 MARC tag.

        Uses GET /bibs endpoint and `controlNumber` query parameter.

        Args:
            keywords:
                a list of MARC control numbers (001 MARC tag) as a comma separated
                string or a list of strings
            deleted:
                whether or not the record has been deleted as a bool
            limit:
                how many records to return. default is 10.
            offset:
                first record to return from results page. default is 0.
            hooks:
                Requests library hook system that can be used for signal event handling,
                see more at: https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

        Returns:
            `requests.Response` object

        """

        controlNumbers = self._prep_multi_keywords(keywords)

        if not keywords:
            raise BookopsPlatformError(
                "Missing required positional argument `keywords`."
            )

        url = self._get_bib_list_url()
        payload: dict[str, Any] = {
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
        keywords: Union[str, list[str], list[int]],
        deleted: bool = False,
        limit: int = 10,
        offset: int = 0,
        hooks: Optional[dict[str, Callable]] = None,
    ) -> requests.Response:
        """
        Makes a request for resources with matching Sierra bib numbers.

        Uses GET /bibs endpoint and `id` query parameter.

        Args:
            keywords:
                a list of sierra bib IDs as a comma separated string or list of strings
            deleted:
                whether or not the record has been deleted as a bool
            limit:
                how many records to return. default is 10.
            offset:
                first record to return from results page. default is 0.
            hooks:
                Requests library hook system that can be used for signal event handling,
                see more at: https://requests.readthedocs.io/en/master/user/advanced/#event-hooks

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
        payload: dict[str, Any] = {
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
