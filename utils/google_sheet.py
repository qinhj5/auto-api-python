# -*- coding: utf-8 -*-
import os
import sys
import gspread
import traceback
from typing import List
import filelock as filelock
from utils.dirs import lock_dir
from utils.logger import logger
from types import TracebackType
from utils.common import get_ext_conf


class GoogleSheet:
    _instance = None

    def __new__(cls, *args, **kwargs) -> None:
        """
        Implement singleton mode.

        Returns:
            None
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, conf_name: str = "google_api") -> None:
        """
        Initialize an instance of the GoogleSheet class.

        Args:
            conf_name (str): The name of the configuration. Defaults to "google_api".

        Returns:
            None
        """
        self._lock = filelock.FileLock(os.path.abspath(os.path.join(lock_dir, "google_sheet.lock")))
        self._conf = get_ext_conf(name=conf_name)
        self._gspread_client = None
        self._sheet_page = None
        self._active_sheet = None
        self._init()

    def __enter__(self) -> 'GoogleSheet':
        """
        Context manager method for entering the context.

        Returns:
            GoogleSheet: The current instance of the GoogleSheet class.
        """
        return self

    def __exit__(self, exc_type: type, exc_val: BaseException, exc_tb: TracebackType) -> None:
        """
        Context manager method for exiting the context.

        Args:
            exc_type (type): The type of the exception (if any) that occurred within the context.
            exc_val (BaseException): The exception object (if any) that occurred within the context.
            exc_tb (TracebackType): The traceback object (if any) associated with the exception.

        Returns:
            None
        """
        if exc_type:
            logger.error(f"""{exc_val}\n{"".join(traceback.format_tb(exc_tb))}""")

    def _init(self) -> None:
        """
        Initialize the gsheet client.

        Returns:
            None
        """
        self._gspread_client = gspread.service_account_from_dict(
            info=self._conf.get("service_info"),
            scopes=[
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/spreadsheets"
            ]
        )
        self._sheet_page = self._gspread_client.open(self._conf.get("google_sheet").get("file_name"))
        self._active_sheet = self._sheet_page.worksheet(self._conf.get("google_sheet").get("sheet_name"))

    def clear_active_sheet(self) -> None:
        """
        Clear the content of the active sheet.

        Returns:
            None
        """
        with self._lock:
            self._active_sheet.clear()

    def create_sheet(self, title: str, rows: int = 100, cols: int = 20) -> None:
        """
        Create a new sheet with the given title.

        Args:
            title (str): The title of the new sheet.
            rows (int): The number of rows in the new sheet (default is 100).
            cols (int): The number of columns in the new sheet (default is 26).

        Returns:
            None
        """
        if title in self.get_sheet_titles():
            logger.error(f"title {title} of sheet dose not exist")
            sys.exit(1)
        else:
            with self._lock:
                self._sheet_page.add_worksheet(title=title, rows=rows, cols=cols)

    def switch_to_sheet(self, title: str) -> bool:
        """
        Switch to the sheet with the specified title.

        Args:
            title (str): The title of the target sheet.

        Returns:
            bool: True if the switch is successful, False otherwise.
        """
        try:
            self._active_sheet = self._sheet_page.worksheet(title)
            return True
        except gspread.exceptions.WorksheetNotFound:
            logger.error(f"sheet with title {title} not found")
            return False

    def insert_rows(self, data: List[list]) -> None:
        """
        Insert rows of data to the active sheet.

        Args:
            data (List[list]): The list of data to be inserted.

        Returns:
            None
        """
        with self._lock:
            self._active_sheet.update(data)

    def delete_sheet(self, title: str) -> bool:
        """
        Delete the sheet with the specified title.

        Args:
            title (str): The title of the sheet to be deleted.

        Returns:
            bool: True if the deletion is successful, False otherwise.
        """
        try:
            with self._lock:
                sheet = self._sheet_page.worksheet(title)
                self._sheet_page.del_worksheet(sheet)
                return True
        except gspread.exceptions.WorksheetNotFound:
            logger.error(f"sheet with title {title} not found")
            return False

    def get_sheet_titles(self) -> List[str]:
        """
        Get a list of titles of all sheets in the spreadsheet.

        Returns:
            List[str]: A list of sheet titles.
        """
        return [i.title for i in self._sheet_page.worksheets()]


if __name__ == "__main__":
    # for the specific file in config, should grant Editor access to service account manually
    logger.info(GoogleSheet().get_sheet_titles())
