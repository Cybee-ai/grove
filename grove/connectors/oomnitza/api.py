# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

"""Oomnitza API client.

As Oomnitza SDK does not currently support the Activities API, this client has been created in
the interim.
"""

import logging
from typing import Dict, Optional

import requests
from grove.exceptions import RequestFailedException
from grove.types import AuditLogEntries, HTTPResponse

API_BASE_URI = "https://{identity}.oomnitza.com"
API_PAGE_SIZE = 200


class Client:
    def __init__(
        self,
        identity: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """Setup a new client.

        :param identity: The name of the Oomnitza organisation.
        :param token: The Oomnitza API token.
        """
        self.logger = logging.getLogger(__name__)
        self.headers = {
            "content-type": "application/json",
            "Authorization2": f"{token}",
        }

        # We need to push the identity into the URI, so we'll keep track of this.
        self._api_base_uri = API_BASE_URI.format(identity=identity)

    def _get(
        self,
        url: str,
        params: Optional[Dict[str, Optional[str]]] = None,
    ) -> HTTPResponse:
        """A GET wrapper to handle retries for the caller.

        :param url: URL to perform the HTTP GET against.
        :param params: HTTP parameters to add to the request.

        :raises RequestFailedException: An HTTP request failed.

        :return: HTTP Response object containing the headers and body of a response.
        """
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as err:
            raise RequestFailedException(err)

        return HTTPResponse(headers=response.headers, body=response.json())

    def get_activites(
        self,
        cursor: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> AuditLogEntries:
        """Fetches a list of signing attempt logs.

        :param cursor: Cursor to use when fetching results. Supersedes other parameters.
        :param from_date: The earliest date an event represented as a UNIX epoch time.

        :return: AuditLogEntries object containing a pagination cursor, and log entries.
        """
        url = f"{self._api_base_uri}/api/v3/activities"

        result = self._get(
            url,
            params={
                "start_date": start_date,
                "end_date": end_date,
                "limit": str(API_PAGE_SIZE),
                "skip": str(cursor),
            },
        )
        # Keep paging until we run out of results.
        data = result.body

        if len(data) == API_PAGE_SIZE:
            cursor += API_PAGE_SIZE
        else:
            cursor = 0

        # Return the cursor and the results to allow the caller to page as required.
        return AuditLogEntries(cursor=cursor, entries=data)  # type: ignore
