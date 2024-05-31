# -*- coding: utf-8 -*-
import csv
import datetime
import json
import os
import random
import shutil
import subprocess
from typing import Any, List, Union

import allure
import filelock
import git
import yaml
from openpyxl.styles import Alignment
from openpyxl.worksheet.worksheet import Worksheet

from utils.dirs import (
    config_dir,
    data_dir,
    lock_dir,
    log_request_dir,
    log_summary_dir,
    project_dir,
    report_dir,
)
from utils.enums import LogLevel
from utils.logger import logger

common_lock = filelock.FileLock(os.path.abspath(os.path.join(lock_dir, f"common.lock")))


def get_env_conf(name: str = None) -> Union[dict, str, list]:
    """
    Get configuration information of environment.

    Args:
        name (str): Configuration item name. Defaults to None.

    Returns:
        Union[dict, str, list]: Configuration item if name is provided, otherwise the entire configuration.
    """
    conf = {}
    conf_path = os.path.abspath(
        os.path.join(config_dir, f"""conf_{os.environ.get("ENV", "test")}.yaml""")
    )

    if not os.path.exists(conf_path):
        logger.error(f"file not found: {conf_path}")
        return conf

    with open(conf_path, "r", encoding="utf-8") as f:
        conf = yaml.safe_load(f)

    if name:
        conf = conf.get(name)

    return conf


def get_ext_conf(name: str = None) -> Union[dict, str, list]:
    """
    Get configuration information of extension.

    Args:
        name (str): Configuration item name. Defaults to None.

    Returns:
        Union[dict, str, list]: Configuration item if name is provided, otherwise the entire configuration.
    """
    conf = {}
    conf_path = os.path.abspath(os.path.join(config_dir, f"conf_ext.yaml"))

    if not os.path.exists(conf_path):
        logger.error(f"file not found: {conf_path}")
        return conf

    with open(conf_path, "r", encoding="utf-8") as f:
        conf = yaml.safe_load(f)

    if name:
        conf = conf.get(name)

    return conf


def get_current_datetime() -> str:
    """
    Get the string representation of the current time.

    Returns:
        str: The string representation of the current time, formatted as "%Y%m%d_%H%M%S".
    """
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(json_path: str) -> Any:
    """
    Load json from a file.

    Args:
        json_path (str): The path to the json file.

    Returns:
        Any: The loaded json data.
    """
    logger.info(f"load json file: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(json_path: str, data: Any) -> None:
    """
    Dump json to a file.

    Args:
        json_path (str): The path to the json file.
        data (Any): The json data to be dumped.

    Returns:
        None
    """
    logger.info(f"dump json file: {json_path}")

    with common_lock:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)


def set_allure_detail(
    body: Any, name: str = "assertion error", level: LogLevel = LogLevel.ERROR
) -> str:
    """
    Set detailed information for Allure report output.

    Args:
        body (Any): Content.
        name (str): Name. Defaults to "assertion error".
        level (LogLevel): Log level for the attachment. Defaults to LogLevel.ERROR.

    Returns:
        None
    """
    if isinstance(body, str):
        attachment_type = allure.attachment_type.TEXT
    else:
        body = json.dumps(body)
        attachment_type = allure.attachment_type.JSON

    allure.attach(body=body, name=name, attachment_type=attachment_type)

    if level == LogLevel.ERROR:
        logger.error(f"{name}: {body}")
    elif level == LogLevel.WARNING:
        logger.warning(f"{name}: {body}")
    elif level == LogLevel.INFO:
        logger.info(f"{name}: {body}")
    else:
        logger.debug(f"{name}: {body}")

    return body


def get_code_modifiers(
    file_path: str, line_range: dict = None, line_number: int = None
) -> List[str]:
    """
    Get the email addresses of the code modifiers according line range or number.

    Args:
        file_path (str): File path.
        line_range (dict): Line range, keys - start_line, end_line.
        line_number (int): Line number.

    Returns:
        List[str]: Email addresses of the code modifiers.
    """
    if not line_range and not line_number:
        raise Exception("miss argument: line_range or line_number")

    modifiers = set()

    try:
        repo = git.Repo(project_dir)
    except Exception as e:
        logger.warning(f"git.not.found: {e}")
        modifiers.add("git.not.found")
    else:
        commit_blames = repo.blame(file=file_path, rev=None)
        row_blames = []
        for commit_blame in commit_blames:
            rows = commit_blame[-1]
            git_commit = commit_blame[0]
            for row in rows:
                row_blames.append(
                    {
                        "code": row,
                        "date": git_commit.committed_datetime.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if bool(int(git_commit.hexsha, 16))
                        else "not.committed.yet",
                        "author": git_commit.author.email
                        if bool(int(git_commit.hexsha, 16))
                        else "not.committed.yet",
                    }
                )

        if line_number:
            start_line = line_number
            end_line = line_number
        else:
            start_line = line_range.get("start_line")
            end_line = line_range.get("end_line")

        for idx in range(start_line, end_line + 1):
            modifiers.add(row_blames[idx]["author"])
    finally:
        return list(modifiers)


def get_csv_data(csv_path: str) -> List[List[str]]:
    """
    Get the data from a CSV file.

    Args:
        csv_path (str): Path of the CSV file.

    Returns:
        List[List[str]]: List of rows in the CSV file, where each row is a list of strings.
    """
    res = []
    csv_path = os.path.abspath(os.path.join(data_dir, csv_path))

    if not os.path.exists(csv_path):
        logger.error(f"file not found: {csv_path}")
        return res

    logger.info(f"get csv data: {csv_path}")

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for _, row in enumerate(reader):
            res.append(row)

    return res


def get_json_data(json_path: str) -> Union[dict, list]:
    """
    Get the data from a json file.

    Args:
        json_path (str): Name of the json file.

    Returns:
       Union[dict, list]: The data from the json file, which can be a dict or a list of dict.
    """
    res = {}
    json_path = os.path.abspath(os.path.join(data_dir, json_path))

    if not os.path.exists(json_path):
        logger.error(f"file not found: {json_path}")
        return res

    logger.info(f"get json data: {json_path}")

    res = load_json(json_path)

    return res


def clean_logs_and_reports() -> None:
    """
    Clean up log files and report files.

    Returns:
        None
    """
    if os.path.exists(report_dir):
        shutil.rmtree(report_dir)

        os.makedirs(report_dir, exist_ok=True)
        open(os.path.abspath(os.path.join(report_dir, ".gitkeep")), "w").close()

    if os.path.exists(log_request_dir):
        shutil.rmtree(log_request_dir)

    if os.path.exists(log_summary_dir):
        shutil.rmtree(log_summary_dir)


def generate_random_string(num: int, charset: str) -> str:
    """
    Generate a random string of length num using the characters specified in the charset parameter.

    Args:
        num (int): The length of the random string to be generated.
        charset (str): A string representing the characters that can be used to generate the random string.
        This parameter can take the following values:
        - string.ascii_letters: includes all uppercase and lowercase letters
        - string.ascii_lowercase: includes only lowercase letters
        - string.ascii_uppercase: includes only uppercase letters
        - string.digits: includes only digits

    Returns:
        str: The generated random string.
    """
    return "".join(random.choice(charset) for _ in range(num))


def set_column_max_width(worksheet: Worksheet) -> None:
    """
    Set the column with max width in the worksheet.

    Args:
        worksheet (Worksheet): The worksheet to adjust the column width.

    Returns:
        None
    """
    for column_cells in worksheet.columns:
        max_length = 0
        column = column_cells[0].column_letter
        for cell in column_cells:
            cell.alignment = Alignment(wrapText=True)

            text = str(cell.value)
            length = len(text[: text.find("\n")])

            if length > max_length:
                max_length = length

        worksheet.column_dimensions[column].width = max_length + 10


def execute_local_command(cmd: str, inp: str = None) -> str:
    """
    Execute a local command and optionally provide input to it.

    Args:
        cmd (str): The command to be executed.
        inp (str): The input to be provided to the command. Defaults to None.

    Returns:
        str: The stdout output of the command.

    """
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    stdout, stderr = proc.communicate(input=f"{inp}\n") if inp else proc.communicate()
    return_code = proc.returncode

    if return_code == 0:
        logger.info(f"execute command success: {cmd}")
    else:
        logger.warning(f"execute command failed: {cmd}")
        logger.error(f"stderr:\n{stderr}")

    return stdout
