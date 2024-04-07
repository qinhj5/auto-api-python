# -*- coding: utf-8 -*-
import allure
import pytest
from utils.logger import logger
from utils.common import get_csv_data, set_assertion_error


class TestGoogleSearchByKeyword:
    @allure.severity("normal")
    @pytest.mark.normal
    @pytest.mark.parametrize("keyword", ["pytest", "requests"])
    def test_get_google_search_by_keyword_using_parameter(self, google_search_api, keyword):
        res = google_search_api.get_google_search_by_keyword(keyword=keyword)
        actual_code = res["status_code"]
        logger.info(f"get_google_search_by_keyword status code: {actual_code}")

        expected_code = 200
        assert actual_code == expected_code, set_assertion_error(
            f"actual: {actual_code}, expected: {expected_code}"
        )

        assert keyword in res["text"], set_assertion_error(
            f"cannot find {keyword} in html content"
        )

    @allure.severity("normal")
    @pytest.mark.normal
    def test_get_google_search_by_keyword_using_data(self, google_search_api):
        rows = get_csv_data(csv_name="keyword")
        for row in rows:
            res = google_search_api.get_google_search_by_keyword(keyword=row[0])
            actual_code = res["status_code"]
            logger.info(f"get_google_search_by_keyword status code: {actual_code}")

            expected_code = 200
            assert actual_code == expected_code, set_assertion_error(
                f"actual: {actual_code}, expected: {expected_code}"
            )

            assert row[0] in res["text"], set_assertion_error(
                f"cannot find {row[0]} in html content"
            )
