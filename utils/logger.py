# -*- coding: utf-8 -*-
import os
import logging
import colorlog
from utils.decorators import log_locker
from logging.handlers import RotatingFileHandler

# get current environment
env = os.environ.get("ENV", "test")

# setup log directory
utils_dir = os.path.dirname(__file__)
project_dir = os.path.abspath(os.path.join(utils_dir, ".."))
log_dir = os.path.abspath(os.path.join(project_dir, "log"))

# setup log path
log_path = os.path.abspath(os.path.join(log_dir, f"{env}.log"))

# setup formatter
log_format = "%(asctime)s - PID:%(process)s - TID:%(thread)s - %(file)s:%(line)d - [%(levelname)s] - %(message)s"
console_formatter = colorlog.ColoredFormatter(
    f"%(log_color)s{log_format}",
    log_colors={
        "DEBUG": "bold_blue",
        "INFO": "bold_green",
        "WARNING": "bold_yellow",
        "ERROR": "bold_red"
    }
)
file_formatter = logging.Formatter(log_format)

# build console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)

# build file handler
file_handler = RotatingFileHandler(log_path,
                                   maxBytes=1024 * 1024 * 10,
                                   backupCount=3,
                                   mode="a",
                                   encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)

# setup logger
logger = logging.getLogger(env)
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# add decorator
logger.debug = log_locker(logger.debug)
logger.info = log_locker(logger.info)
logger.warning = log_locker(logger.warning)
logger.error = log_locker(logger.error)
