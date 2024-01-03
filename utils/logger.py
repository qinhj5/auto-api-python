# -*- coding: utf-8 -*-
import os
import logging
import colorlog
import multiprocessing
from logging.handlers import RotatingFileHandler

# setup directory
utils_dir = os.path.dirname(__file__)
project_dir = os.path.abspath(os.path.join(utils_dir, ".."))
log_dir = os.path.abspath(os.path.join(project_dir, "log"))
os.makedirs(log_dir, exist_ok=True)

# setup file
test_log_path = os.path.abspath(os.path.join(log_dir, "test.log"))

# setup formatter
log_format = "%(asctime)s - P:%(process)s - T:%(thread)s - %(filename)s:%(lineno)d - [%(levelname)s] - %(message)s"
file_formatter = logging.Formatter(log_format)

# build console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = colorlog.ColoredFormatter(
    f"%(log_color)s{log_format}",
    log_colors={
        "DEBUG": "bold_blue",
        "INFO": "bold_green",
        "WARNING": "bold_yellow",
        "ERROR": "bold_red"
    }
)
console_handler.setFormatter(console_formatter)

# build file handler
file_handler = RotatingFileHandler(test_log_path,
                                   maxBytes=1024 * 1024 * 10,
                                   backupCount=3,
                                   mode="a",
                                   encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)

# setup logger
logger = multiprocessing.get_logger()
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)
