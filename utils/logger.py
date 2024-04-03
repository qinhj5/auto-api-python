# -*- coding: utf-8 -*-
import os
import logging
import colorlog
from utils.decorators import log_locker
from logging.handlers import RotatingFileHandler

ENV = os.environ.get("ENV", "test")
LOG_FORMAT = "%(asctime)s - PID:%(process)s - TID:%(thread)s - %(file)s:%(line)d - [%(levelname)s] - %(message)s"

CONSOLE_HANDLER = logging.StreamHandler()
CONSOLE_HANDLER.setLevel(logging.INFO)
CONSOLE_FORMATTER = colorlog.ColoredFormatter(
    f"%(log_color)s{LOG_FORMAT}",
    log_colors={
        "DEBUG": "bold_blue",
        "INFO": "bold_green",
        "WARNING": "bold_yellow",
        "ERROR": "bold_red"
    }
)
CONSOLE_HANDLER.setFormatter(CONSOLE_FORMATTER)

FILE_HANDLER = RotatingFileHandler(os.path.abspath(os.path.join(os.path.dirname(__file__), f"../log/{ENV}.log")),
                                   maxBytes=1024 * 1024 * 10,
                                   backupCount=3,
                                   mode="a",
                                   encoding="utf-8")
FILE_HANDLER.setLevel(logging.DEBUG)
FILE_FORMATTER = logging.Formatter(LOG_FORMAT)
FILE_HANDLER.setFormatter(FILE_FORMATTER)

logger = logging.getLogger(ENV)
logger.setLevel(logging.DEBUG)
logger.addHandler(CONSOLE_HANDLER)
logger.addHandler(FILE_HANDLER)

logger.debug = log_locker(logger.debug)
logger.info = log_locker(logger.info)
logger.warning = log_locker(logger.warning)
logger.error = log_locker(logger.error)
