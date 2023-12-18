# -*- coding: utf-8 -*-
import os
import sys
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


utils_dir = os.path.dirname(__file__)
project_path = os.path.abspath(os.path.join(utils_dir, ".."))
sys.path.append(project_path)
