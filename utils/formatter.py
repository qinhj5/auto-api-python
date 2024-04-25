# -*- coding: utf-8 -*-
import os
import sys
import traceback
from pathlib import Path

import black
import isort

from utils.dirs import project_dir
from utils.logger import logger


def format_python_files(target_dir: str) -> None:
    """
    Format all Python files in the target directory.

    Args:
        target_dir (str): The path of the target directory.

    Returns:
        None
    """
    for root, dirs, files in os.walk(target_dir):
        if "venv" in root:
            continue
        for file in files:
            file_path = os.path.abspath(os.path.join(root, file))
            if file_path.endswith(".py"):
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_code = f.read()
                formatted_code = black.format_str(raw_code, mode=black.FileMode())
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(formatted_code)
                isort.file(
                    Path(file_path),
                    config=isort.Config(
                        known_third_party=["api", "config"], profile="black"
                    ),
                )
                logger.info(f"formatted: {file_path}")


if __name__ == "__main__":
    try:
        sys.path.append(project_dir)
        format_python_files(target_dir=project_dir)
    except Exception as e:
        logger.error(f"{e}\n{traceback.format_exc()}")
