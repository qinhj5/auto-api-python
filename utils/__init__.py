# -*- coding: utf-8 -*-
import os
import sys
from typing import Any

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
