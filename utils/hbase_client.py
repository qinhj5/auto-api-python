# -*- coding: utf-8 -*-
import os
import traceback
from types import TracebackType

import filelock
import pexpect as pexpect

from utils.common import get_env_conf
from utils.dirs import lock_dir
from utils.logger import logger


class HBaseClient:
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

    def __init__(self, conf_name: str = "driver_ip") -> None:
        """
        Initialize an instance of the HBaseClient class.

        Args:
            conf_name (str): The name of the configuration. Defaults to "driver_ip".

        Returns:
            None
        """
        self._lock = filelock.FileLock(
            os.path.abspath(os.path.join(lock_dir, f"{conf_name}.lock"))
        )
        self._driver_ip = get_env_conf(name=conf_name)
        self._connect_driver()
        self._enter_client()

    def __enter__(self) -> "HBaseClient":
        """
        Context manager method for entering the context.

        Returns:
            HBaseClient: The current instance of the HBaseClient class.
        """
        return self

    def __exit__(
        self, exc_type: type, exc_val: BaseException, exc_tb: TracebackType
    ) -> None:
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

        self.close()

    def _connect_driver(self) -> None:
        """
        Establish an SSH connection to the driver.

        Returns:
            None
        """
        self._child = pexpect.spawn(
            f"ssh {self._driver_ip}", encoding="utf-8", codec_errors="ignore"
        )
        index = self._child.expect("Last login", timeout=60)
        if index == 0:
            logger.info(f"login {self._driver_ip} success")
        else:
            logger.error(f"login {self._driver_ip} failed")

    def _enter_client(self) -> None:
        """
        Enter the client application.

        Returns:
            None
        """
        self._child.sendline("hbase shell")
        index = self._child.expect("Version", timeout=60)
        if index == 0:
            logger.info(f"enter client success")
        else:
            logger.error(f"enter client failed")

    def execute(self, command: str, expected: str) -> bool:
        """
        Execute a command in the HBase client.

        Args:
            command (str): The command to execute in the SSH session.
            expected (str): The expected output after executing the command.

        Returns:
            bool: True if the command executed successfully, False otherwise.
        """
        if not self._child.isalive():
            self._connect_driver()
            self._enter_client()

        self._child.buffer = ""
        try:
            self._child.sendline(command)
            self._child.expect(expected, timeout=60)
        except Exception as e:
            logger.error(f"{e}\n{traceback.format_exc()}")
            return False
        else:
            logger.info(f"execute command success: {command}")
            return True

    def close(self) -> None:
        """
        Close the HBase client.

        Returns:
            None
        """
        if self._child:
            self._child.close()
