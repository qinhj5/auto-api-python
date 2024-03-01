# -*- coding: utf-8 -*-
import os
import csv
import json
import time
import yaml
import shutil
import random
import allure
import datetime
import subprocess
from utils.logger import logger
from typing import Any, List, Union, Dict
from openpyxl.worksheet.worksheet import Worksheet
from utils.dirs import config_dir, data_dir, report_dir, log_request_dir, log_summary_dir


def set_env(env: str) -> None:
    """
    Set the environment variable.

    Args:
        env (str): The value to set for the environment variable.

    Returns:
        None
    """
    os.environ["ENV"] = env


def get_env() -> str:
    """
    Get the environment variable.

    Returns:
        str: The value of the environment variable.
    """
    env = os.environ.get("ENV", "test")
    return env


def get_env_conf(name: str = None) -> dict:
    """
    Get configuration information of environment.

    Args:
        name (str): Configuration item name. Defaults to None.

    Returns:
        dict: Configuration item dictionary if `name` is provided, otherwise the entire configuration dictionary.
    """
    conf_path = os.path.abspath(os.path.join(config_dir, f"conf_{get_env()}.yml"))

    with open(conf_path, "r", encoding="utf-8") as f:
        conf = yaml.safe_load(f)
        if name:
            return conf.get(name)
        return conf


def get_ext_conf(name: str = None) -> dict:
    """
    Get configuration information of extension.

    Args:
        name (str): Configuration item name. Defaults to None.

    Returns:
        dict: Configuration item dictionary if `name` is provided, otherwise the entire configuration dictionary.
    """
    conf_path = os.path.abspath(os.path.join(config_dir, f"conf_ext.yml"))

    with open(conf_path, "r", encoding="utf-8") as f:
        conf = yaml.safe_load(f)
        if name:
            return conf.get(name)
        return conf


def get_current_datetime() -> str:
    """
    Get the string representation of the current time.

    Returns:
        str: The string representation of the current time, formatted as "%Y-%m-%d %H:%M:%S".
    """
    current_datetime = datetime.datetime.now()
    formatted_datetime = current_datetime.strftime("%Y%m%d_%H%M%S")
    return formatted_datetime


def get_current_timestamp() -> int:
    """
    Get the timestamp of the current time (milliseconds).

    Returns:
        int: The timestamp of the current time (milliseconds).
    """
    milliseconds = int(time.time() * 1000)
    return milliseconds


def is_json_object(obj: Any) -> bool:
    """
    Check if an object is a JSON object.

    Args:
        obj: Object.

    Returns:
        bool: True if the object is a list, tuple, or dictionary; False otherwise.
    """
    if isinstance(obj, list) or isinstance(obj, tuple) or isinstance(obj, dict):
        return True
    else:
        return False


def is_json_string(string: str) -> bool:
    """
    Check if a string is a JSON string.

    Args:
        string (str): String.

    Returns:
        bool: True if the string is a valid JSON string; False otherwise.
    """
    try:
        json.loads(string)
        return True
    except ValueError:
        return False


def loads_json_string(string: str) -> Any:
    """
    Parse a JSON string into an object.

    Args:
        string (str): JSON string.

    Returns:
        Any: Parsed object.
    """
    obj = json.loads(string)
    return obj


def get_formatted_json_string(data: dict) -> str:
    """
    Get the formatted JSON string.

    Args:
        data (dict): Dictionary data.

    Returns:
        str: The formatted JSON string.
    """
    json_str = json.dumps(data, indent=4, sort_keys=True)
    return json_str


def print_formatted_json_string(data: dict) -> None:
    """
    Print the formatted JSON string.

    Args:
        data (dict): Dictionary data.

    Returns:
        None
    """
    json_str = json.dumps(data, indent=4, sort_keys=True)
    print(json_str)


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
        body = get_formatted_json_string(body)
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
        body = json.dumps(body)
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
            line_range = {"start_line": line_number, "end_line": line_number}

        for line_number in range(line_range["start_line"], line_range["end_line"] + 1):
            command = f"git blame --line-porcelain -L {line_number},{line_number} {file_path}"
            result = subprocess.run(command, shell=True, capture_output=True)

            if result.returncode != 0:
                modifiers.add(f"execute.command.error")
            else:
                output = result.stdout
                code_modifier = output.split("\n")[2].split()[1][1:-1]
                modifiers.add(code_modifier)

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
    logger.info(f"read csv file: {csv_path}")
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for _, row in enumerate(reader):
            res.append(row)
    return res


def get_json_data(json_name: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Get the data from a json file.

    Args:
        json_name (str): Name of the json file (without the extension).

    Returns:
        Union[Dict[str, Any], List[Dict[str, Any]]]: The data from the json file, which can be a dict or a list of dict.
    """
    res = None
    json_path = os.path.abspath(os.path.join(data_dir, f"{json_name}.json"))
    logger.info(f"read json file: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, (dict, list)):
            res = data
    return res


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


def clean_logs_and_reports() -> None:
    """
    Clean up log files and report files.

    Returns:
        None
    """
    if os.path.exists(report_dir):
        shutil.rmtree(report_dir)
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


def adjust_column_width(worksheet: Worksheet) -> None:
    """
    Adjusts the column width in the worksheet.

    Args:
        worksheet (Worksheet): The worksheet to adjust the column width.

    Returns:
        None
    """
    for column_cells in worksheet.columns:
        max_length = 0
        column = column_cells[0].column_letter
        for cell in column_cells:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except Exception as e:
                logger.error(e)
        adjusted_width = (max_length + 2)
        worksheet.column_dimensions[column].width = adjusted_width
