# -*- coding: utf-8 -*-
from typing import Type, Callable


def singleton(cls: Type) -> Callable:
    instances = {}

    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrapper
