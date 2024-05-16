# -*- coding: utf-8 -*-
import inspect
import os
from datetime import datetime
from typing import Callable

import filelock
import pytz

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
        file_path, line_number = inspect.getframeinfo(inspect.currentframe().f_back)[:2]
        extra = {
            "time": datetime.now(pytz.timezone("Asia/Shanghai")),
            "file": os.path.basename(file_path),
            "line": line_number,
        }
        with filelock.FileLock(LOCK_PATH):
            return func(*args, **kwargs, extra=extra)

    return wrapper
