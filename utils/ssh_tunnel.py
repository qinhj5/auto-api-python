# -*- coding: utf-8 -*-
import paramiko
import threading
from typing import Tuple
from utils import get_conf, logger
from paramiko.channel import ChannelStdinFile, ChannelFile, ChannelStderrFile


class SSHTunel:
    _instance = None

    def __new__(cls, *args, **kwargs) -> None:
        """
        Implement singleton mode.

        Returns:
            None
        """
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        """
        Initialize an instance of the SSHTunel class.

        Returns:
            None
        """
        self._ssh_conf = get_conf(name="ssh")
        self._ssh_tunnel = None
        self._lock = threading.Lock()

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
        if self._ssh_tunnel is None:
            self._ssh_tunnel = SSHTunel._create_ssh_tunnel(self._ssh_conf)
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
        Close the ssh tunnel.

        Returns:
            None
        """
        with self._lock:
            if self._ssh_tunnel:
                self._ssh_tunnel.close()
