# -*- coding: utf-8 -*-
import os
import traceback
from types import TracebackType
from typing import Tuple

import filelock
import paramiko
from paramiko.channel import ChannelFile, ChannelStderrFile, ChannelStdinFile
from utils.common import get_env_conf
from utils.dirs import lock_dir
from utils.logger import logger


class TunnelShell:
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

    def __init__(self, conf_name: str = "ssh") -> None:
        """
        Initialize an instance of the TunnelShell class.

        Args:
            conf_name (str): The name of the configuration. Defaults to "ssh".

        Returns:
            None
        """
        self._lock = filelock.FileLock(
            os.path.abspath(os.path.join(lock_dir, f"{conf_name}.lock"))
        )
        self._conf = get_env_conf(name=conf_name)
        self._tunnel_client = None

    def __enter__(self) -> "TunnelShell":
        """
        Context manager method for entering the context.

        Returns:
            TunnelShell: The current instance of the TunnelShell class.
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
    def _create_tunnel_client(ssh_conf: dict) -> paramiko.SSHClient:
        """
        Create a tunnel client connection.

        Args:
            ssh_conf (dict): SSH configuration information.

        Returns:
            paramiko.SSHClient: tunnel client object.
        """
        tunnel_client = paramiko.SSHClient()
        tunnel_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_key = ssh_conf.get("ssh_key")

        if ssh_key is None:
            private_key = None
        else:
            private_key = paramiko.RSAKey.from_private_key_file(ssh_conf.get("ssh_key"))

        tunnel_client.connect(
            hostname=ssh_conf["ssh_host"],
            port=ssh_conf["ssh_port"],
            username=ssh_conf["ssh_user"],
            pkey=private_key,
            password=ssh_conf.get("ssh_password"),
        )

        return tunnel_client

    def _execute(
        self, command: str
    ) -> Tuple[ChannelStdinFile, ChannelFile, ChannelStderrFile]:
        """
        Execute a command on the tunnel client.

        Args:
            command (str): The command to execute.

        Returns:
            Tuple[ChannelStdinFile, ChannelFile, ChannelStderrFile]: A tuple contained the input, output, and error.
        """
        try:
            if self._tunnel_client is None:
                self._tunnel_client = TunnelShell._create_tunnel_client(self._conf)
        except Exception as exception:
            logger.error(exception)
            self.close()
        else:
            stdin, stdout, stderr = self._tunnel_client.exec_command(command)
            return stdin, stdout, stderr

    def execute_command(self, command: str) -> ChannelStdinFile:
        """
        Execute a command and log the output.

        Args:
            command (str): The command to execute.

        Returns:
            ChannelStdinFile: The input channel of the tunnel client.
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
        Close the tunnel client.

        Returns:
            None
        """
        if self._tunnel_client:
            self._tunnel_client.stop()
