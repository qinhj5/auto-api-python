# -*- coding: utf-8 -*-
import pytest
from config.conf import Global
from api.google_search.google_search_api import GoogleSearchAPI


@pytest.fixture(scope="package")
def google_search_api():
    google_search_api = GoogleSearchAPI(
        base_url=Global.constants.BASE_URL, headers=Global.constants.HEADERS
    )
    return google_search_api
