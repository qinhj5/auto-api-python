# -*- coding: utf-8 -*-
import os
import csv
import json
import time
import yaml
import allure
import datetime
from utils import logger
from typing import Any, List


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
    env = os.environ.get("ENV", "staging")
    return env


def get_conf(name: str = None) -> dict:
    """
    Get configuration information.

    Args:
        name (str): Configuration item name. Defaults to None.

    Returns:
        dict: Configuration information dictionary.

    Raises:
        FileNotFoundError: Raised when the configuration file does not exist.
    """
    utils_dir = os.path.dirname(__file__)
    conf_path = os.path.abspath(os.path.join(utils_dir, f"../config/conf_{get_env()}.yml"))

    with open(conf_path, mode="r", encoding="utf-8") as f:
        conf = yaml.safe_load(f)
        if name:
            return conf[name]
        return conf


def get_current_datetime() -> str:
    """
    Get the string representation of the current time.

    Returns:
        str: The string representation of the current time, formatted as "%Y-%m-%d %H:%M:%S".
    """
    current_datetime = datetime.datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
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
        string: String.

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
        string: JSON string.

    Returns:
        Any: Parsed object.
    """
    obj = json.loads(string)
    return obj


def get_formatted_json_string(data: dict) -> str:
    """
    Get the formatted JSON string.

    Args:
        data: Dictionary data.

    Returns:
        str: The formatted JSON string.
    """
    json_str = json.dumps(data, indent=4, sort_keys=True)
    return json_str


def print_formatted_json_string(data: dict) -> None:
    """
    Print the formatted JSON string.

    Args:
        data: Dictionary data.

    Returns:
        None
    """
    json_str = json.dumps(data, indent=4, sort_keys=True)
    print(json_str)


def set_console_detail(name: str, body: Any) -> None:
    """
    Set detailed information for console output.

    Args:
        name: Name.
        body: Content.

    Returns:
        None
    """
    string = "-" * 64
    middle_start = (len(string) - len(name)) // 2
    middle_end = middle_start + len(name)
    print_str = string[:middle_start] + name + string[middle_end:]
    if is_json_object(body):
        body = get_formatted_json_string(body)
    else:
        body = str(body)
    print(f"\n{print_str}\n{body}\n{string}")


def set_allure_detail(name: str, body: Any) -> None:
    """
    Set detailed information for Allure report output.

    Args:
        name: Name.
        body: Content.

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
        name: Name.
        body: Content.

    Returns:
        None
    """
    set_console_detail(name, body)
    set_allure_detail(name, body)


def get_code_modifier(file_path: str, line_number: int) -> str:
    """
    Get the email address of the code modifier.

    Args:
        file_path: File path.
        line_number: Line number.

    Returns:
        str: Email address of the code modifier.
    """
    command = f"git blame --line-porcelain -L {line_number},{line_number} {file_path}"
    output = os.popen(command).read()
    try:
        author_mail = output.split("\n")[2].split()[1][1:-1]
    except Exception as e:
        return f"no record ({e})"

    return author_mail


def get_csv_data(csv_name: str) -> List[List[str]]:
    """
    Get the data from a CSV file.

    Args:
        csv_name: Name of the CSV file (without the extension).

    Returns:
        List[List[str]]: List of rows in the CSV file, where each row is a list of strings.
    """
    res = []
    utils_dir = os.path.dirname(__file__)
    data_dir = os.path.abspath(os.path.join(utils_dir, "../data"))
    csv_path = os.path.abspath(os.path.join(data_dir, f"{csv_name}.csv"))
    logger.info(f"read csv file: {csv_path}")
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for index, row in enumerate(reader, 1):
            res.append(row)
    return res
