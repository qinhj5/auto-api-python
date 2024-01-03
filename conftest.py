# -*- coding: utf-8 -*-
import os
import time
import pytest
import inspect
from connection.mysql_connection import MysqlConnection
from utils import set_allure_and_console_output, get_code_modifier


@pytest.fixture(scope="session")
def db():
    db = MysqlConnection()
    yield db
    db.close()


@pytest.fixture(scope="function", autouse=True)
def code_modifier(request):
    function_path = inspect.getfile(request.function.__code__)
    set_allure_and_console_output(name="function path", body=function_path)

    file_path = inspect.getfile(request.module)
    line_number = request.function.__code__.co_firstlineno
    set_allure_and_console_output(name="last modified by", body=get_code_modifier(file_path, line_number))


def pytest_terminal_summary(terminalreporter, config):
    if config.pluginmanager.get_plugin("xdist"):
        if hasattr(config, "workerinput"):
            process_name = config.workerinput["workerid"]
        elif hasattr(config, "slaveinput"):
            process_name = config.slaveinput["slaveid"]
        else:
            process_name = "main"
    else:
        process_name = "main"

    project_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.abspath(os.path.join(project_dir, "log"))
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.abspath(os.path.join(log_dir, f"summary_{process_name}.log"))

    num_passed = len(terminalreporter.stats.get("passed", []))
    num_failed = len(terminalreporter.stats.get("failed", []))
    num_error = len(terminalreporter.stats.get("error", []))
    num_skipped = len(terminalreporter.stats.get("skipped", []))
    num_collected = num_passed + num_failed + num_error + num_skipped

    with open(log_path, "w", encoding="utf-8") as f:
        f.writelines("Total number of test cases: {}\n".format(num_collected))
        f.writelines("Number of passed test cases: {}\n".format(num_passed))
        f.writelines("Number of failed test cases: {}\n".format(num_failed))
        f.writelines("Number of error test cases: {}\n".format(num_error))
        f.writelines("Number of skipped test cases: {}\n".format(num_skipped))

        duration = time.time() - terminalreporter._sessionstarttime
        f.writelines("Duration (seconds): {:.2f}".format(duration))
