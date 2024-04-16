# -*- coding: utf-8 -*-
import pytest
from api.google_search.google_search_api import GoogleSearchAPI
from config.conf import Global


@pytest.fixture(scope="package")
def google_search_api():
    google_search_api = GoogleSearchAPI(
        base_url=Global.CONSTANTS.BASE_URL, headers=Global.CONSTANTS.HEADERS
    )
    return google_search_api
