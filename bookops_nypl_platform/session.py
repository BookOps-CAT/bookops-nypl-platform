# -*- coding: utf-8 -*-

"""
bookops_nypl_platform.session
=============================
This module provides a session functionality used for making requests
to NYPL Platform API
"""

from typing import Tuple, Type, Union

import requests

from . import __title__, __version__
from .authorize import PlatformToken
from .errors import BookopsPlatformError


class PlatformSession(requests.Session):
    """
    Opens a session with NYPL Platform API and provides methods
    to send requests to it.

    Args:

    """

    def __init__(
        self,
        authorization: Type[PlatformToken],
        target: str = "prod",
        agent: str = None,
        timeout: Union[int, float, Tuple[int, int], Tuple[float, float]] = None,
    ):
        requests.Session.__init__(self)

        self.token = authorization
        if type(self.token).__name__ != "PlatformToken":
            raise BookopsPlatformError(
                "Invalid authorization. Argument must be an instance of `PlatformToken` obj."
            )

        if target == "prod":
            self.base_url = "https://platform.nypl.org/api/v0.1"
        elif target == "dev":
            self.base_url = "https://dev-platform.nypl.org/api/v0.1"
        else:
            raise BookopsPlatformError(
                "Invalid `target` argument passed into a Platform session."
            )

        if agent is None:
            self.headers.update({"User-Agent": f"{__title__}/{__version__}"})
        elif type(agent) is str:
            self.headers.update({"User-Agent": agent})
        else:
            raise BookopsPlatformError("Argument `agent` must be a string.")

        self.timeout = timeout
        if self.timeout is None:
            self.timeout = (3, 3)
