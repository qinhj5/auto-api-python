# -*- coding: utf-8 -*-
import os
import sys
from config.conf import Global


# setup project directory
config_dir = os.path.dirname(__file__)
project_dir = os.path.abspath(os.path.join(config_dir, ".."))
sys.path.append(project_dir)
