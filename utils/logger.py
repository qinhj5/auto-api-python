# -*- coding: utf-8 -*-
import os
import logging
import colorlog

# Logger setup
logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

# Directory setup
utils_dir = os.path.dirname(__file__)
project_path = os.path.abspath(os.path.join(utils_dir, ".."))
log_dir = os.path.abspath(os.path.join(project_path, "log"))
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.abspath(os.path.join(log_dir, "test.log"))

# File handler
file_handler = logging.FileHandler(log_path)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
    log_colors={
        "DEBUG": "bold_green",
        "INFO": "bold_green",
        "WARNING": "bold_yellow",
        "ERROR": "bold_red"
    }
)
console_handler.setFormatter(console_formatter)

# Adding handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
