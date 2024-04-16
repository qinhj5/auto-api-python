# -*- coding: utf-8 -*-
from http import HTTPStatus
from json import JSONDecodeError, loads
from typing import Any, Dict

import curlify
import requests
from utils.common import set_allure_detail
from utils.enums import LogLevel


class BaseAPI:
    def __init__(self, base_url: str, headers: dict) -> None:
        """
        Initialize an instance of the BaseAPI class.

        Args:
            base_url (str): The base url of the API.
            headers (Dict[str, Any]): The header information for the requests.

        Returns:
            None
        """
        self._base_url = base_url
        self._headers = headers

    def _send_request(
        self,
        uri: str,
        method: str,
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        json: Dict[str, Any] = None,
        headers: Dict[str, Any] = None,
        files: Any = None,
    ) -> Dict[str, Any]:
        """
        Send a prepared request.

        Args:
            uri (str): The URI of the request.
            method (str): The method of the request.
            data (Dict[str, Any]): The data of the request as a dictionary.
            params (Dict[str, Any]): The url parameters of the request as a dictionary.
            json (Dict[str, Any]): The json data of the request as a dictionary.
            headers (Dict[str, Any]): The header information of the request as a dictionary.
            files (Any): The files to be included in the request.

        Returns:
            Dict[str, Any]: The response content of the request as a dictionary.
        """
        total_headers = self._headers.copy()
        if headers:
            total_headers.update(headers)

        url = f"{self._base_url}{uri}"
        set_allure_detail(name="url", body=url, level=LogLevel.INFO)
        set_allure_detail(name="headers", body=total_headers, level=LogLevel.INFO)
        set_allure_detail(
            name="request body", body=params or data or json, level=LogLevel.INFO
        )

        request = requests.Request(
            url=url,
            method=method,
            headers=total_headers,
            data=data,
            params=params,
            json=json,
            files=files,
        )
        prepared_request = requests.Session().prepare_request(request)

        with requests.Session().send(prepared_request, timeout=600) as r:
            set_allure_detail(
                name="curl",
                body=curlify.to_curl(r.request, compressed=True),
                level=LogLevel.INFO,
            )

            status = f"name: {HTTPStatus(r.status_code).name}, code: {r.status_code}"
            set_allure_detail(name="status code", body=status, level=LogLevel.INFO)

            if len(r.text) < 1024 * 256:
                try:
                    response_body = loads(r.text)
                    response_body.update({"status_code": r.status_code})
                except JSONDecodeError:
                    response_body = {"status_code": r.status_code, "text": r.text}
            else:
                response_body = {
                    "status_code": r.status_code,
                    "text": "response is too long to display",
                }

            set_allure_detail(
                name="response body", body=response_body, level=LogLevel.INFO
            )

            return response_body
