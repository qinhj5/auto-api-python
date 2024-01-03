# -*- coding: utf-8 -*-
import os
import sys
from utils.decorators import singleton
from utils.logger import logger, file_formatter
from utils.common import (get_env,
                          set_env,
                          get_conf,
                          get_csv_data,
                          get_json_data,
                          is_json_string,
                          get_code_modifier,
                          loads_json_string,
                          set_assertion_error,
                          get_current_datetime,
                          set_allure_and_console_output,
                          )

# setup project directory
utils_dir = os.path.dirname(__file__)
project_dir = os.path.abspath(os.path.join(utils_dir, ".."))
sys.path.append(project_dir)
