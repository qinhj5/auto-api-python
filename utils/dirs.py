# -*- coding: utf-8 -*-
import os

utils_dir = os.path.dirname(__file__)
project_dir = os.path.abspath(os.path.join(utils_dir, ".."))

log_dir = os.path.abspath(os.path.join(project_dir, "log"))

log_request_dir = os.path.abspath(os.path.join(log_dir, "request"))
os.makedirs(log_request_dir, exist_ok=True)

log_summary_dir = os.path.abspath(os.path.join(log_dir, "summary"))
os.makedirs(log_summary_dir, exist_ok=True)

tmp_dir = os.path.abspath(os.path.join(project_dir, "tmp"))
data_dir = os.path.abspath(os.path.join(project_dir, "data"))
config_dir = os.path.abspath(os.path.join(project_dir, "config"))
template_dir = os.path.abspath(os.path.join(project_dir, "template"))

report_dir = os.path.abspath(os.path.join(project_dir, "report"))
report_raw_dir = os.path.abspath(os.path.join(report_dir, "raw"))
report_html_dir = os.path.abspath(os.path.join(report_dir, "html"))
report_sheet_dir = os.path.abspath(os.path.join(report_dir, "sheet"))
report_locust_dir = os.path.abspath(os.path.join(report_dir, "locust"))

venv_dir = os.path.abspath(os.path.join(project_dir, "venv"))
venv_bin_dir = os.path.abspath(os.path.join(venv_dir, "bin"))

lock_dir = os.path.abspath(os.path.join(project_dir, "lock"))
os.makedirs(lock_dir, exist_ok=True)
