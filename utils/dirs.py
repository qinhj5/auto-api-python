# -*- coding: utf-8 -*-
import os

utils_dir = os.path.dirname(__file__)
project_dir = os.path.abspath(os.path.join(utils_dir, ".."))

log_dir = os.path.abspath(os.path.join(project_dir, "log"))
data_dir = os.path.abspath(os.path.join(project_dir, "data"))
config_dir = os.path.abspath(os.path.join(project_dir, "config"))

report_dir = os.path.abspath(os.path.join(project_dir, "report"))
report_raw_dir = os.path.abspath(os.path.join(report_dir, "raw"))
report_html_dir = os.path.abspath(os.path.join(report_dir, "html"))

lock_dir = os.path.abspath(os.path.join(project_dir, "lock"))
os.makedirs(lock_dir, exist_ok=True)
