# -*- coding: utf-8 -*-
import inspect
import os
from typing import Callable

import filelock
from utils.dirs import lock_dir

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
        file_name = os.path.basename(file_path)
        extra = {"file": file_name, "line": line_number}
        with filelock.FileLock(LOCK_PATH):
            return func(*args, **kwargs, extra=extra)

    return wrapper
