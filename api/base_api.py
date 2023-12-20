# -*- coding: utf-8 -*-
import curlify
import requests
from http import HTTPStatus
from typing import Any, Dict
from utils import set_allure_and_console_output, get_current_datetime, is_json_string, loads_json_string


class BaseAPI:
    def __init__(self, base_url: str, headers: dict) -> None:
        """
        Initialize an instance of the BaseAPI class.

        Args:
            base_url (str): The base URL of the API.
            headers (Dict[str, Any]): The header information for the requests.

        Returns:
            None
        """
        self.base_url = base_url
        self.headers = headers

    def send_prepared_request(self, uri: str,
                              method: str,
                              data: Dict[str, Any] = None,
                              params: Dict[str, Any] = None,
                              json: Dict[str, Any] = None,
                              headers: Dict[str, Any] = None,
                              files: Any = None) -> Dict[str, Any]:
        """
        Send a prepared request.

        Args:
            uri (str): The URI of the request.
            method (str): The method of the request.
            data (Dict[str, Any], optional): The data of the request as a dictionary.
            params (Dict[str, Any], optional): The URL parameters of the request as a dictionary.
            json (Dict[str, Any], optional): The JSON data of the request as a dictionary.
            headers (Dict[str, Any], optional): The header information of the request as a dictionary.
            files (Any, optional): The files to be included in the request.

        Returns:
            Dict[str, Any]: The response content of the request as a dictionary.
        """
        total_headers = self.headers.copy()
        if headers:
            total_headers.update(headers)

        url = f"{self.base_url}{uri}"
        set_allure_and_console_output(name="url", body=url)
        set_allure_and_console_output(name="headers", body=total_headers)
        set_allure_and_console_output(name="request body", body=params or data or json)

        request = requests.Request(
            url=url,
            method=method,
            headers=total_headers,
            data=data,
            params=params,
            json=json,
            files=files
        )
        prepared_request = requests.Session().prepare_request(request)

        set_allure_and_console_output(name="start time", body=get_current_datetime())

        with requests.Session().send(prepared_request, timeout=600) as r:
            set_allure_and_console_output(name="curl", body=curlify.to_curl(r.request, compressed=True))

            status = f"name: {HTTPStatus(r.status_code).name}, code: {r.status_code}"
            set_allure_and_console_output(name="status code", body=status)

            if is_json_string(r.text):
                response_body = loads_json_string(r.text)
                response_body.update({"status_code": r.status_code})
            else:
                response_body = {"status_code": r.status_code, "text": r.text}
            set_allure_and_console_output(name="response body", body=response_body)

            set_allure_and_console_output(name="end time", body=get_current_datetime())

            return response_body
