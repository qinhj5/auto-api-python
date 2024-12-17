# -*- coding: utf-8 -*-
import os
import traceback
from types import TracebackType
from typing import Tuple

import filelock
import paramiko
from paramiko.channel import ChannelFile, ChannelStderrFile, ChannelStdinFile
from sshtunnel import SSHTunnelForwarder

from utils.common import get_env_conf
from utils.dirs import lock_dir
from utils.logger import logger


class DriverShell:
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

    def __init__(
        self, ip_conf_name: str = "driver_ip", ssh_conf_name: str = "ssh"
    ) -> None:
        """
        Initialize an instance of the DriverShell class.

        Args:
            ip_conf_name (str): The name of the IP configuration. Defaults to "driver_ip".
            ssh_conf_name (str): The name of the SSH configuration. Defaults to "ssh".

        Returns:
            None
        """
        self._lock = filelock.FileLock(
            os.path.abspath(os.path.join(lock_dir, f"{ip_conf_name}.lock"))
        )
        self._ip = get_env_conf(name=ip_conf_name)
        self._ssh_conf = get_env_conf(name=ssh_conf_name)
        self._driver_client = None
        self._tunnel_forwarder = None

    def __enter__(self) -> "DriverShell":
        """
        Context manager method for entering the context.

        Returns:
            DriverShell: The current instance of the DriverShell class.
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

    @staticmethod
    def _create_driver_client(
        ssh_conf: dict, ip: str
    ) -> Tuple[SSHTunnelForwarder, paramiko.SSHClient]:
        """
        Create a driver client connection.

        Args:
            ssh_conf (dict): SSH configuration information.
            ip (str): The IP of driver.

        Returns:
            Tuple[SSHTunnelForwarder, paramiko.SSHClient]: A tuple containing the SSH tunnel and driver client objects.
        """
        driver_client = paramiko.SSHClient()
        driver_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        driver_client.load_system_host_keys()
        ssh_key = ssh_conf.get("ssh_key")

        if ssh_key is None:
            private_key = None
        else:
            private_key = paramiko.RSAKey.from_private_key_file(ssh_conf.get("ssh_key"))

        tunnel_forwarder = SSHTunnelForwarder(
            (ssh_conf["ssh_host"], ssh_conf["ssh_port"]),
            ssh_username=ssh_conf["ssh_user"],
            ssh_pkey=private_key,
            remote_bind_address=(ip, 22),
        )
        tunnel_forwarder.start()

        driver_client.connect(
            hostname="127.0.0.1",
            port=tunnel_forwarder.local_bind_port,
            username=ssh_conf["ssh_user"],
            pkey=private_key,
            password=ssh_conf.get("ssh_password"),
        )

        return tunnel_forwarder, driver_client

    def _execute(
        self, command: str
    ) -> Tuple[ChannelStdinFile, ChannelFile, ChannelStderrFile]:
        """
        Execute a command on the driver client.

        Args:
            command (str): The command to execute.

        Returns:
            Tuple[ChannelStdinFile, ChannelFile, ChannelStderrFile]: A tuple contained the input, output, and error.
        """
        try:
            if self._tunnel_forwarder is None or self._driver_client is None:
                self.close()
                (
                    self._tunnel_forwarder,
                    self._driver_client,
                ) = DriverShell._create_driver_client(self._ssh_conf, self._ip)
        except Exception as exception:
            logger.error(f"{exception}\n{traceback.format_exc()}")
            self.close()
        else:
            stdin, stdout, stderr = self._driver_client.exec_command(command)
            return stdin, stdout, stderr

    def execute_command(self, command: str) -> ChannelStdinFile:
        """
        Execute a command and log the output.

        Args:
            command (str): The command to execute.

        Returns:
            ChannelStdinFile: The input channel of the driver client.
        """
        with self._lock:
            stdin, stdout, stderr = self._execute(command)
            logger.info(f"executed command: {command}")
            output = stdout.read().decode("utf-8").strip()
            error = stderr.read().decode("utf-8").strip()
            if output:
                logger.info(f"""standard output: {output}""")
            if error:
                logger.error(f"""standard error: {error}""")
            return stdin

    def close(self) -> None:
        """
        Close the driver client.

        Returns:
            None
        """
        if self._driver_client:
            self._driver_client.close()
        if self._tunnel_forwarder:
            self._tunnel_forwarder.close()
