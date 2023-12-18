# -*- coding: utf-8 -*-
import pytest
from utils import get_csv_data


@pytest.mark.parametrize("keyword", ["pytest", "requests"])
def test_get_google_search_by_keyword_using_parameter(google_search_api, keyword):
    res = google_search_api.get_google_search_by_keyword(keyword=keyword)
    assert res["status_code"] == 200
    assert keyword in res["text"]


def test_get_google_search_by_keyword_using_data(google_search_api):
    rows = get_csv_data(csv_name="keyword")
    for row in rows:
        res = google_search_api.get_google_search_by_keyword(keyword=row[0])
        assert res["status_code"] == 200
        assert row[0] in res["text"]
