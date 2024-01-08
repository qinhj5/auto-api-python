# -*- coding: utf-8 -*-
from typing import Dict, Any
from api.base_api import BaseAPI


class GoogleSearchAPI(BaseAPI):
    def get_google_search_by_keyword(self, keyword: str) -> Dict[str, Any]:
        """
        Get Google search results by keyword

        Args:
            self
            keyword (str): The keyword to search for, multiple keywords separated by comma, e.g. keyword1,keyword2

        Returns:
            Dict[str, Any]: The response content of the request as a dictionary.
        """
        params_dict = {"q": keyword}
        return self._send_request(
            uri="/search", method="GET", params=params_dict
        )
