# -*- coding: utf-8 -*-
import os
import csv
import json
import time
import yaml
import shutil
import random
import allure
import filelock
import datetime
import subprocess
from utils.logger import logger
from typing import Any, List, Union
from openpyxl.styles import Alignment
from openpyxl.worksheet.worksheet import Worksheet
from utils.dirs import config_dir, data_dir, report_dir, log_request_dir, log_summary_dir, lock_dir

common_lock = filelock.FileLock(os.path.abspath(os.path.join(lock_dir, f"common.lock")))


def get_env_conf(name: str = None) -> dict:
    """
    Get configuration information of environment.

    Args:
        name (str): Configuration item name. Defaults to None.

    Returns:
        dict: Configuration item dictionary if name is provided, otherwise the entire configuration dictionary.
    """
    conf = {}
    conf_path = os.path.abspath(os.path.join(config_dir, f"""conf_{os.environ.get("ENV", "test")}.yml"""))

    if not os.path.exists(conf_path):
        logger.error(f"file not found: {conf_path}")
        return conf

    with open(conf_path, "r", encoding="utf-8") as f:
        conf = yaml.safe_load(f)

    if name:
        conf = conf.get(name)

    return conf


def get_ext_conf(name: str = None) -> dict:
    """
    Get configuration information of extension.

    Args:
        name (str): Configuration item name. Defaults to None.

    Returns:
        dict: Configuration item dictionary if name is provided, otherwise the entire configuration dictionary.
    """
    conf = {}
    conf_path = os.path.abspath(os.path.join(config_dir, f"conf_ext.yml"))

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
        str: The string representation of the current time, formatted as "%Y-%m-%d %H:%M:%S".
    """
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def get_current_timestamp() -> int:
    """
    Get the timestamp of the current time (milliseconds).

    Returns:
        int: The timestamp of the current time (milliseconds).
    """
    return int(time.time() * 1000)


def is_json_object(obj: Any) -> bool:
    """
    Check if an object is a json object.

    Args:
        obj (Any): Object.

    Returns:
        bool: True if the object is a list or dictionary; False otherwise.
    """
    return isinstance(obj, list) or isinstance(obj, dict)


def is_json_string(string: str) -> bool:
    """
    Check if a string is a json string.

    Args:
        string (str): String.

    Returns:
        bool: True if the string is a valid json string; False otherwise.
    """
    try:
        json.loads(string)
    except ValueError:
        return False
    else:
        return True


def loads_json(string: str) -> Any:
    """
    Parse a json string into an object.

    Args:
        string (str): json string.

    Returns:
        Any: Parsed object.
    """
    return json.loads(string)


def dumps_json(data: Any) -> str:
    """
    Get the formatted json string.

    Args:
        data (Any): Dictionary data.

    Returns:
        str: The formatted json string.
    """
    return json.dumps(data)


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


def set_console_detail(name: str, body: Any) -> None:
    """
    Set detailed information for console output.

    Args:
        name (str): Name.
        body (Any): Content.

    Returns:
        None
    """
    start_str = name.center(64, "-")
    end_str = "-" * 64
    if is_json_object(body):
        body = dumps_json(body)
    else:
        body = str(body)
    print(f"\n{start_str}\n{body}\n{end_str}")


def set_allure_detail(name: str, body: Any) -> None:
    """
    Set detailed information for Allure report output.

    Args:
        name (str): Name.
        body (Any): Content.

    Returns:
        None
    """
    attachment_type = allure.attachment_type.TEXT
    if is_json_object(body):
        body = dumps_json(body)
        attachment_type = allure.attachment_type.JSON
    else:
        body = str(body)

    allure.attach(body=body, name=name, attachment_type=attachment_type)


def set_allure_and_console_output(name: str, body: Any) -> None:
    """
    Set detailed information for both Allure report and console output.

    Args:
        name (str): Name.
        body (Any): Content.

    Returns:
        None
    """
    set_console_detail(name, body)
    set_allure_detail(name, body)


def set_assertion_error(detail: str) -> str:
    """
    Set detailed information for both Allure report and console output in case of an assertion error.

    Args:
        detail (str): Error detail.

    Returns:
        str: Error detail.
    """
    set_allure_and_console_output(name="assertion error", body=detail)
    return detail


def get_code_modifiers(file_path: str, line_range: dict = None, line_number: int = None) -> List[str]:
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

    is_installed = False
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        output = result.stdout.strip()
        if output.startswith("git version"):
            is_installed = True
        else:
            modifiers.add(f"git.not.found")
    except FileNotFoundError:
        modifiers.add(f"git.not.found")

    if is_installed:

        if line_number:
            start_line = line_number
            end_line = line_number
        else:
            start_line = line_range.get("start_line")
            end_line = line_range.get("end_line")

        command = f"git blame --line-porcelain -L {start_line},{end_line} {file_path}"
        result = subprocess.run(command, shell=True, capture_output=True)

        if result.returncode != 0:
            modifiers.add(f"execute.command.error")
        else:
            output = result.stdout.decode("utf-8")
            lines = output.split("\n")

            for line in lines:
                if line.startswith("author-mail"):
                    modifiers.add(line.split()[1][1:-1])

    return list(modifiers)


def get_csv_data(csv_name: str) -> List[List[str]]:
    """
    Get the data from a CSV file.

    Args:
        csv_name (str): Name of the CSV file (without the extension).

    Returns:
        List[List[str]]: List of rows in the CSV file, where each row is a list of strings.
    """
    res = []
    csv_path = os.path.abspath(os.path.join(data_dir, f"{csv_name}.csv"))

    if not os.path.exists(csv_path):
        logger.error(f"file not found: {csv_path}")
        return res

    logger.info(f"get csv data: {csv_path}")

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for _, row in enumerate(reader):
            res.append(row)

    return res


def get_json_data(json_name: str) -> Union[dict, list]:
    """
    Get the data from a json file.

    Args:
        json_name (str): Name of the json file (without the extension).

    Returns:
       Union[dict, list]: The data from the json file, which can be a dict or a list of dict.
    """
    res = {}
    json_path = os.path.abspath(os.path.join(data_dir, f"{json_name}.json"))

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
            length = len(text[:text.find("\n")])

            if length > max_length:
                max_length = length

        worksheet.column_dimensions[column].width = max_length + 10
