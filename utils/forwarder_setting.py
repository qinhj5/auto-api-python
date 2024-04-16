# -*- coding: utf-8 -*-
import getpass
import subprocess
import sys
import traceback

from utils.common import get_env_conf
from utils.logger import logger


class ForwarderSetting:
    def __init__(
        self,
        server_conf_name: str = "servers",
        ssh_conf_name: str = "ssh",
        use_loopback: bool = True,
    ) -> None:
        """
        Initialize an instance of the ForwarderSetting class.

        Args:
            server_conf_name (str): The name of the server configuration. Defaults to "servers".
            ssh_conf_name (str): The name of the ssh configuration. Defaults to "ssh".
            use_loopback (bool): Flag indicating whether to use the loopback interface for forwarding. Defaults to True.

        Returns:
            None
        """
        self._servers_list = get_env_conf(name=server_conf_name)
        self._ssh_conf = get_env_conf(name=ssh_conf_name)
        self._use_loopback = use_loopback

    def _build_command(self) -> list:
        """
        Build the SSH command with port forwarding.

        Returns:
            list: The SSH command with port forwarding.
        """
        forwards = []
        for server in self._servers_list:
            ip = server.get("ip")
            port = server.get("port")
            if self._use_loopback:
                forwards += ["-L", f"{ip}:{port}:{ip}:{port}"]
            else:
                forwards += ["-L", f"{port}:{ip}:{port}"]

        command = (
            ["ssh"]
            + forwards
            + [
                "-N",
                "-f",
                f"""{self._ssh_conf.get("ssh_user")}@{self._ssh_conf.get("ssh_host")}""",
            ]
        )

        return command

    @staticmethod
    def _get_command_pids(command: list) -> list:
        """
        Get the process IDs (PIDs) of the running processes that match the specified command.

        Args:
            command (list): The command to match.

        Returns:
            list: The list of process IDs (PIDs) of the matching processes.
        """
        target_cmd = " ".join(command)
        grep_cmd = f"""ps aux | grep "{target_cmd}" """
        process = subprocess.Popen(grep_cmd, shell=True, stdout=subprocess.PIPE)
        logger.info(f"executed: {grep_cmd}")
        output, _ = process.communicate()

        pids = []
        lines = output.strip().decode().split("\n")
        for line in lines:
            if target_cmd in line and "grep" not in line:
                pids.append(line.split()[1])

        return pids

    def _disconnect_ssh_tunnel(self) -> None:
        """
        Disconnect the specified servers via ssh tunnel.

        Returns:
            None
        """
        command = self._build_command()

        pids = ForwarderSetting._get_command_pids(command)
        if pids:
            for pid in pids:
                subprocess.call(f"kill {pid}", shell=True)
            logger.info(f"""killed: {" ".join(command)}""")
        else:
            logger.warning(f"""no result for {" ".join(command)}""")

    def _connect_ssh_tunnel(self) -> None:
        """
        Connect the specified servers via ssh tunnel.

        Returns:
            None
        """
        command = self._build_command()

        pids = ForwarderSetting._get_command_pids(command)
        if len(pids) == 0:
            subprocess.call(command)
            logger.info(f"""executed: {" ".join(command)}""")
        else:
            logger.warning(f"""existed for {" ".join(command)}""")

    def _remove_local_interfaces(self) -> None:
        """
        Remove local network interfaces/aliases for the specified servers.

        Returns:
            None
        """
        password = getpass.getpass(
            "please enter sudo password (possible plaintext display): "
        )
        for server in self._servers_list:
            if sys.platform == "darwin":
                command = ["sudo", "ifconfig", "lo0", "-alias", server.get("ip")]
            else:
                command = [
                    "sudo",
                    "ip",
                    "addr",
                    "del",
                    server.get("ip") + "/32",
                    "dev",
                    "lo",
                ]

            proc = subprocess.Popen(
                ["sudo", "-S"] + command,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            proc.communicate(password + "\n")
            logger.info(f"""executed: {" ".join(command)}""")

    def _add_local_interfaces(self) -> None:
        """
        Add local network interfaces/aliases for the specified servers.

        Returns:
            None
        """
        password = getpass.getpass(
            "please enter sudo password (possible plaintext display): "
        )
        for server in self._servers_list:
            if sys.platform == "darwin":
                command = ["sudo", "ifconfig", "lo0", "alias", server.get("ip")]
            else:
                command = [
                    "sudo",
                    "ip",
                    "addr",
                    "add",
                    server.get("ip") + "/32",
                    "dev",
                    "lo",
                ]

            proc = subprocess.Popen(
                ["sudo", "-S"] + command,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            proc.communicate(password + "\n")
            logger.info(f"""executed: {" ".join(command)}""")

    def deactivate_forwarder(self) -> None:
        """
        Deactivate forwarder.

        Returns:
            None
        """
        if self._use_loopback:
            self._remove_local_interfaces()
        self._disconnect_ssh_tunnel()

    def activate_forwarder(self) -> None:
        """
        Activate forwarder.

        Returns:
            None
        """
        if self._use_loopback:
            self._add_local_interfaces()
        self._connect_ssh_tunnel()


if __name__ == "__main__":
    try:
        ForwarderSetting().activate_forwarder()
    except Exception as e:
        logger.error(f"{e}\n{traceback.format_exc()}")
