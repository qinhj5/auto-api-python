# -*- coding: utf-8 -*-
import paramiko
import traceback
import threading
from typing import Tuple
from utils.logger import logger
from types import TracebackType
from utils.common import get_conf
from paramiko.channel import ChannelStdinFile, ChannelFile, ChannelStderrFile


class SSHTunnel:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs) -> None:
        """
        Implement singleton mode.

        Returns:
            None
        """
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, ssh_conf_name: str = "ssh") -> None:
        """
        Initialize an instance of the SSHTunnel class.

        Args:
            ssh_conf_name (str): The name of the SSH configuration. Defaults to "ssh".

        Returns:
            None
        """
        self._ssh_conf = get_conf(name=ssh_conf_name)
        self._ssh_tunnel = None

    def __enter__(self) -> 'SSHTunnel':
        """
        Context manager method for entering the context.

        Returns:
            SSHTunnel: The current instance of the SSHTunnel class.
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
            logger.error(f"an exception of type {exc_type} occurred: {exc_val}")

        if exc_tb:
            logger.error("".join(traceback.format_tb(exc_tb)))

        self.close()

    @staticmethod
    def _create_ssh_tunnel(ssh_conf: dict) -> paramiko.SSHClient:
        """
        Create an SSH tunnel connection.

        Args:
            ssh_conf (dict): SSH configuration information.

        Returns:
            paramiko.SSHClient: SSH tunnel object.
        """
        ssh_tunnel = paramiko.SSHClient()
        ssh_tunnel.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_key = ssh_conf.get("ssh_key")

        if ssh_key is None:
            private_key = None
        else:
            private_key = paramiko.RSAKey.from_private_key_file(ssh_conf.get("ssh_key"))

        ssh_tunnel.connect(hostname=ssh_conf["ssh_host"],
                           port=ssh_conf["ssh_port"],
                           username=ssh_conf["ssh_user"],
                           pkey=private_key,
                           password=ssh_conf.get("ssh_password"))

        return ssh_tunnel

    def _execute(self, command: str) -> Tuple[ChannelStdinFile, ChannelFile, ChannelStderrFile]:
        """
        Execute a command on the SSH tunnel.

        Args:
            command (str): The command to execute.

        Returns:
            Tuple[ChannelStdinFile, ChannelFile, ChannelStderrFile]: A tuple contained the input, output, and error.
        """
        try:
            if self._ssh_tunnel is None:
                self._ssh_tunnel = SSHTunnel._create_ssh_tunnel(self._ssh_conf)
        except Exception as e:
            logger.error(f"{e}\n{traceback.format_exc()}")
            self.close()
        else:
            stdin, stdout, stderr = self._ssh_tunnel.exec_command(command)
            return stdin, stdout, stderr

    def execute_command(self, command: str) -> ChannelStdinFile:
        """
        Execute a command and log the output.

        Args:
            command (str): The command to execute.

        Returns:
            ChannelStdinFile: The input channel of the SSH tunnel.
        """
        with SSHTunnel._lock:
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
        Close the ssh tunnel.

        Returns:
            None
        """
        with SSHTunnel._lock:
            if self._ssh_tunnel:
                self._ssh_tunnel.close()
