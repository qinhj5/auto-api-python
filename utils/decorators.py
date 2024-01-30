# -*- coding: utf-8 -*-
import os
import filelock
from typing import Type, Callable

utils_dir = os.path.dirname(__file__)
project_dir = os.path.abspath(os.path.join(utils_dir, ".."))
lock_dir = os.path.abspath(os.path.join(project_dir, "lock"))
os.makedirs(lock_dir, exist_ok=True)
log_lock_path = os.path.abspath(os.path.join(lock_dir, "log.lock"))
log_lock = filelock.FileLock(log_lock_path)


def log_locker(func: Callable) -> Callable:
    """
    Decorator function to lock access to a function using a log_lock.

    Args:
        func (Callable): The function to be decorated.

    Returns:
        Callable: The wrapper function that locks access to the decorated function.
    """
    def wrapper(*args, **kwargs):
        with log_lock:
            return func(*args, **kwargs)
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
