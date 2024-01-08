# -*- coding: utf-8 -*-
import os
import sys
from typing import Any
from utils.decorators import singleton
from utils.logger import logger, file_formatter
from utils.email_notification import send_email
from utils.mysql_connection import MysqlConnection
from utils.common import (get_env,
                          set_env,
                          get_conf,
                          clean_logs,
                          get_csv_data,
                          get_json_data,
                          is_json_string,
                          get_code_modifier,
                          loads_json_string,
                          set_assertion_error,
                          get_current_datetime,
                          set_allure_and_console_output,
                          )

# setup project directory
utils_dir = os.path.dirname(__file__)
project_dir = os.path.abspath(os.path.join(utils_dir, ".."))
sys.path.append(project_dir)


# define a cache
cache = {}


def set_cache(key: str, value: Any) -> None:
    """
    Set a value in the cache.

    Args:
        key (str): The key to set.
        value (Any): The value to set.

    Returns:
        None
    """
    cache[key] = value


def get_cache(key: str) -> Any:
    """
    Retrieve a value from the cache.

    Args:
        key (str): The key to retrieve.

    Returns:
        Any: The value associated with the key, or None if the key is not found.
    """
    return cache.get(key, None)
