# -*- coding: utf-8 -*-
import os
import csv
import json
import time
import yaml
import glob
import random
import allure
import datetime
import subprocess
from utils.logger import logger
from typing import Any, List, Union, Dict
from utils.dirs import config_dir, data_dir, log_dir


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


def get_conf(name: str = None) -> Union[dict, str]:
    """
    Get configuration information.

    Args:
        name (str): Configuration item name. Defaults to None.

    Returns:
        Union[dict, str]: Configuration information dictionary if `name` is provided,
        otherwise the entire configuration dictionary as a string.

    Raises:
        FileNotFoundError: Raised when the configuration file does not exist.
    """
    conf_path = os.path.abspath(os.path.join(config_dir, f"conf_{get_env()}.yml"))

    with open(conf_path, mode="r", encoding="utf-8") as f:
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


def get_code_modifier(file_path: str, line_number: int) -> str:
    """
    Get the email address of the code modifier.

    Args:
        file_path (str): File path.
        line_number (int): Line number.

    Returns:
        str: Email address of the code modifier.
    """
    command = f"git blame --line-porcelain -L {line_number},{line_number} {file_path}"

    try:
        result = subprocess.run(command, shell=True, capture_output=True, encoding="utf-8")
        if result.returncode != 0:
            logger.info(f"No git info in un-versioned file. Please ignore. Exit status: {result.returncode}")
            return "(No git info in un-versioned file.)"
        else:
            output = result.stdout
            code_modifier = output.split("\n")[2].split()[1][1:-1]
            return code_modifier
    except subprocess.CalledProcessError as e:
        logger.error(f"Error occurred during command execution: {e}")
        return "(An error occurred during command execution.)"


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


def clean_logs() -> None:
    """
    Clean up log files in the log directory.

    Removes log files with names containing "request" or "summary" from the log directory.

    Returns:
        None
    """
    for file_path in glob.glob(os.path.join(log_dir, "*.log")):
        file_name: str = os.path.basename(file_path)

        if "request" in file_name or "summary" in file_name:
            os.remove(file_path)


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
