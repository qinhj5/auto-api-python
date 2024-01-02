# -*- coding: utf-8 -*-
import os
import logging
import colorlog

# Logger setup
logger = logging.getLogger("utils.logger")
logger.setLevel(logging.DEBUG)

# Directory setup
utils_dir = os.path.dirname(__file__)
project_dir = os.path.abspath(os.path.join(utils_dir, ".."))
log_dir = os.path.abspath(os.path.join(project_dir, "log"))
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.abspath(os.path.join(log_dir, "test.log"))

# Set log format
log_format = "%(asctime)s - P:%(process)s - T:%(thread)s - %(filename)s:%(lineno)d - [%(levelname)s] - %(message)s"

# File handler
file_handler = logging.FileHandler(log_path)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(log_format)
file_handler.setFormatter(file_formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
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

# Adding handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
