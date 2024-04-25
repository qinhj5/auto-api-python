# -*- coding: utf-8 -*-
import pytest

from api.google_search.google_search_api import GoogleSearchAPI
from config.conf import Global


@pytest.fixture(scope="package")
def google_search_api():
    return GoogleSearchAPI(
        base_url=Global.CONSTANTS.BASE_URL, headers=Global.CONSTANTS.HEADERS
    )
