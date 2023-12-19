# -*- coding: utf-8 -*-
import os
import sys
import logging
import colorlog
from utils.logger import logger
from utils.common import (get_env,
                          set_env,
                          get_conf,
                          set_allure_and_console_output,
                          get_current_datetime,
                          is_json_string,
                          loads_json_string,
                          get_code_modifier,
                          get_csv_data)
from utils.decorators import singleton


# Directory setup
utils_dir = os.path.dirname(__file__)
project_path = os.path.abspath(os.path.join(utils_dir, ".."))
sys.path.append(project_path)
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

# Removing all handlers
for handler in logging.getLogger("").handlers:
    logging.getLogger("").removeHandler(handler)

# Adding handlers to the logger
logging.getLogger("").addHandler(file_handler)
logging.getLogger("").addHandler(console_handler)
logging.getLogger("").setLevel(level=logging.DEBUG)
