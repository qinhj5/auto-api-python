# -*- coding: utf-8 -*-
import os
import sys
from utils.logger import logger
from utils.decorators import singleton
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

# Path setup
utils_dir = os.path.dirname(__file__)
project_path = os.path.abspath(os.path.join(utils_dir, ".."))
sys.path.append(project_path)
