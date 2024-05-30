# -*- coding: utf-8 -*-
import allure
import pytest

from utils.common import get_csv_data, set_allure_detail
from utils.logger import logger


class TestGetSearch:
    @allure.severity("critical")
    @pytest.mark.critical
    @pytest.mark.smoke
    @pytest.mark.get_search
    def test_get_search(self, google_search_api):
        res = google_search_api.get_search()
        actual_code = res["status_code"]
        logger.info(f"get_search status code: {actual_code}")

        expected_code = 200
        assert actual_code == expected_code, set_allure_detail(
            f"actual: {actual_code}, expected: {expected_code}"
        )

    @allure.severity("normal")
    @pytest.mark.normal
    @pytest.mark.parametrize("keyword", ["python", "pytest"])
    def test_get_search_by_parameter(self, google_search_api, keyword):
        res = google_search_api.get_search(keyword=keyword)
        actual_code = res["status_code"]
        logger.info(f"get_search status code: {actual_code}")

        expected_code = 200
        assert actual_code == expected_code, set_allure_detail(
            f"actual: {actual_code}, expected: {expected_code}"
        )

        assert keyword in res["text"], set_allure_detail(
            f"cannot find {keyword} in html content"
        )

    @allure.severity("normal")
    @pytest.mark.normal
    @pytest.mark.parametrize("csv_path", ["google_search/keywords.csv"])
    def test_get_search_by_csv_data(self, google_search_api, csv_path):
        keywords = get_csv_data(csv_path=csv_path)

        for keyword, *_ in keywords:
            res = google_search_api.get_search(keyword=keyword)
            actual_code = res["status_code"]
            logger.info(f"get_search status code: {actual_code}")

            expected_code = 200
            assert actual_code == expected_code, set_allure_detail(
                f"actual: {actual_code}, expected: {expected_code}"
            )

            assert keyword in res["text"], set_allure_detail(
                f"cannot find {keyword} in html content"
            )
