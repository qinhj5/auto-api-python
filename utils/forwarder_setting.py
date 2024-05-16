# -*- coding: utf-8 -*-
import getpass
import os
import sys
import traceback

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


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

    def _build_command(self) -> str:
        """
        Build the SSH command with port forwarding.

        Returns:
            str: The SSH command with port forwarding.
        """
        forwards = []
        for server in self._servers_list:
            ip = server.get("ip")
            port = server.get("port")
            if self._use_loopback:
                forwards += ["-L", f"{ip}:{port}:{ip}:{port}"]
            else:
                forwards += ["-L", f"{port}:{ip}:{port}"]

        command_list = (
            ["ssh"]
            + forwards
            + [
                "-N",
                "-f",
                f"""{self._ssh_conf.get("ssh_user")}@{self._ssh_conf.get("ssh_host")}""",
            ]
        )

        return " ".join(command_list)

    @staticmethod
    def _get_command_pids(command: str) -> list:
        """
        Get the process IDs (PIDs) of the running processes that match the specified command.

        Args:
            command (str): The command to match.

        Returns:
            list: The list of process IDs (PIDs) of the matching processes.
        """
        grep_cmd = f"""ps aux | grep "{command}" """
        stdout = execute_local_command(grep_cmd)

        pids = []
        lines = stdout.strip().split("\n")
        for line in lines:
            if command in line and "grep" not in line:
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
                execute_local_command(f"kill {pid}")
            logger.info(f"""killed: {command}""")
        else:
            logger.warning(f"""no result for {command}""")

    def _connect_ssh_tunnel(self) -> None:
        """
        Connect the specified servers via ssh tunnel.

        Returns:
            None
        """
        command = self._build_command()

        pids = ForwarderSetting._get_command_pids(command)
        if len(pids) == 0:
            execute_local_command(command)
        else:
            logger.warning(f"""existed for {command}""")

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
                command_list = ["sudo", "ifconfig", "lo0", "-alias", server.get("ip")]
            elif sys.platform == "linux":
                command_list = [
                    "sudo",
                    "ip",
                    "addr",
                    "del",
                    server.get("ip") + "/32",
                    "dev",
                    "lo",
                ]
            else:
                logger.error("only support macOS and Linux")
                sys.exit(1)

            command = " ".join(["sudo", "-S"] + command_list)
            execute_local_command(command, inp=password)

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
                command_list = ["sudo", "ifconfig", "lo0", "alias", server.get("ip")]
            elif sys.platform == "linux":
                command_list = [
                    "sudo",
                    "ip",
                    "addr",
                    "add",
                    server.get("ip") + "/32",
                    "dev",
                    "lo",
                ]
            else:
                logger.error("only support macOS and Linux")
                sys.exit(1)

            command = " ".join(["sudo", "-S"] + command_list)
            execute_local_command(command, inp=password)

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
    from utils.common import execute_local_command, get_env_conf
    from utils.logger import logger

    try:
        ForwarderSetting().activate_forwarder()
    except Exception as e:
        logger.error(f"{e}\n{traceback.format_exc()}")
