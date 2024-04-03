# -*- coding: utf-8 -*-
import os
import inspect
import filelock
from utils.dirs import lock_dir
from typing import Type, Callable

LOCK_PATH = os.path.abspath(os.path.join(lock_dir, "log.lock"))


def log_locker(func: Callable) -> Callable:
    """
    Decorator function to lock access to a function using a log_lock.

    Args:
        func (Callable): The function to be decorated.

    Returns:
        Callable: The wrapper function that locks access to the decorated function.
    """
    def wrapper(*args, **kwargs):
        frame = inspect.currentframe().f_back
        file_path, line_number, _, _ = inspect.getframeinfo(frame)[:4]
        file_name = file_path.split("/")[-1]
        extra = {"file": file_name, "line": line_number}
        with filelock.FileLock(LOCK_PATH):
            return func(*args, **kwargs, extra=extra)

    return wrapper


def singleton(cls: Type) -> Callable:
    """
    Implement singleton mode.

    Args:
        cls (Type): The class to be decorated.

    Returns:
        Callable: The wrapper function for creating the singleton object.
    """
    instances = {}

    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrapper
