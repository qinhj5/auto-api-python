# -*- coding: utf-8 -*-
import os
import sys
import traceback
from datetime import datetime

import requests

from config.conf import Global
from utils.common import dump_json, get_current_datetime, load_json
from utils.dirs import tmp_dir
from utils.logger import logger


class SwaggerDiff:
    def __init__(self, swagger_url: str) -> None:
        """
        Initialize the class.

        Args:
            swagger_url (str): The url of the swagger file.

        Returns:
            None
        """
        self._swagger_url = swagger_url
        self._swagger_diff_dir = os.path.abspath(os.path.join(tmp_dir, "swagger_diff"))
        self._history_swagger_dir = os.path.abspath(
            os.path.join(tmp_dir, "history_swagger")
        )
        self._new_json_path = os.path.abspath(
            os.path.join(self._history_swagger_dir, f"{get_current_datetime()}.json")
        )
        self._old_json_path = self._find_old_swagger_json_path()
        self._current_swagger_json = self._get_swagger_json()

    def _get_swagger_json(self) -> dict:
        """
        Get swagger json data by making a request to the specified swagger url.

        Returns:
            dict: Total data of swagger.
        """
        response = requests.get(self._swagger_url, headers=Global.CONSTANTS.HEADERS)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error("cannot request swagger url")
            sys.exit(1)

    def _find_old_swagger_json_path(self) -> str:
        """
        Find the path of the oldest swagger json file.

        Returns:
            str: The absolute path of the oldest swagger json file, or an empty string if no json file is found.
        """
        json_list = []
        os.makedirs(self._history_swagger_dir, exist_ok=True)
        for filename in os.listdir(self._history_swagger_dir):
            if filename.endswith(".json"):
                date_string = filename.split(".")[0]
                timestamp = datetime.strptime(date_string, "%Y%m%d_%H%M%S").timestamp()
                json_list.append({"datetime": date_string, "timestamp": timestamp})

        if not json_list:
            return ""

        sorted(json_list, key=lambda x: x["timestamp"])
        return os.path.abspath(
            os.path.join(
                self._history_swagger_dir, f"""{json_list[-1]["datetime"]}.json"""
            )
        )

    def _load_old_swagger_json(self) -> dict:
        """
        Load the old swagger json data.

        Returns:
            dict: The loaded old swagger json data, or None if the file does not exist.
        """
        if os.path.exists(self._old_json_path):
            data = load_json(self._old_json_path)
        else:
            data = None
        return data

    @staticmethod
    def _compare_dicts(old_dict: dict, new_dict: dict) -> tuple:
        """
        Compare two dictionaries and identify the differences.

        Args:
            old_dict (dict): The old dictionary.
            new_dict (dict): The new dictionary.

        Returns:
            tuple: A tuple contained removed_dicts, added_dicts and changed_dicts
        """
        keys_only_in_old_dict = set(old_dict.keys()) - set(new_dict.keys())
        keys_only_in_new_dict = set(new_dict.keys()) - set(old_dict.keys())
        common_keys = set(old_dict.keys()) & set(new_dict.keys())

        removed_dicts = {key: old_dict[key] for key in keys_only_in_old_dict}
        added_dicts = {key: new_dict[key] for key in keys_only_in_new_dict}
        changed_dicts = {
            key: {"old": old_dict[key], "new": new_dict[key]}
            for key in common_keys
            if old_dict[key] != new_dict[key]
        }

        return removed_dicts, added_dicts, changed_dicts

    def _get_swagger_diff(self) -> tuple:
        """
        Get the difference between the old and new swagger json.

        Returns:
            tuple: A tuple containing the difference between the paths in the old and new swagger json.
        """
        old_swagger_json = self._load_old_swagger_json()
        if old_swagger_json is None:
            logger.info(f"first swagger json created")
            dump_json(self._new_json_path, self._current_swagger_json)
            sys.exit(1)

        new_swagger_json = self._current_swagger_json
        return SwaggerDiff._compare_dicts(
            old_swagger_json.get("paths"), new_swagger_json.get("paths")
        )

    def swagger_scanning(self) -> None:
        """
        Perform swagger scanning and identify the changes between old and new swagger json.

        Returns:
            None
        """
        removed_dicts, added_dicts, changed_dicts = self._get_swagger_diff()

        if (not removed_dicts) & (not added_dicts) & (not changed_dicts):
            logger.info("current swagger remain unchanged")
        else:
            result = {
                "old": self._old_json_path,
                "new": self._new_json_path,
                "removed": removed_dicts,
                "added": added_dicts,
                "changed": changed_dicts,
            }
            os.makedirs(self._swagger_diff_dir, exist_ok=True)
            swagger_diff_path = os.path.abspath(
                os.path.join(self._swagger_diff_dir, f"{get_current_datetime()}.json")
            )
            logger.info(f"swagger changed")
            dump_json(swagger_diff_path, result)

            dump_json(self._new_json_path, self._current_swagger_json)


if __name__ == "__main__":
    try:
        # swagger_url is the link to the swagger api-docs
        SwaggerDiff(swagger_url="").swagger_scanning()
    except Exception as e:
        logger.error(f"{e}\n{traceback.format_exc()}")
