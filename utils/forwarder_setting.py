# -*- coding: utf-8 -*-
import sys
import getpass
import subprocess
from utils.logger import logger
from utils.common import get_env_conf


class ForwarderSetting:
    def __init__(self, conf_name: str = "forwarder_servers") -> None:
        """
        Initialize the class.

        Args:
            conf_name (str): The name of the configuration to retrieve.

        Returns:
            None
        """
        self._forwarder_servers = get_env_conf(name=conf_name)

    def _build_command(self) -> list:
        """
        Build the SSH command with port forwarding.

        Returns:
            list: The SSH command with port forwarding.
        """
        forwards = []
        for server in self._forwarder_servers:
            forwards += ["-L", f"{server}:{server}"]

        ssh_conf = get_env_conf("ssh")
        command = ["ssh"] + forwards + ["-N", "-f", f"""{ssh_conf.get("ssh_user")}@{ssh_conf.get("ssh_host")}"""]

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
            logger.info(f"killed: {command}")
        else:
            logger.warning(f"no result for {command}")

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
            logger.info(f"executed: {command}")
        else:
            logger.warning(f"existed for {command}")

    def _remove_local_interfaces(self) -> None:
        """
        Remove local network interfaces/aliases for the specified servers.

        Returns:
            None
        """
        password = getpass.getpass("please enter sudo password (possible plaintext display): ")
        for server in self._forwarder_servers:
            if sys.platform == "darwin":
                command = ["sudo", "ifconfig", "lo0", "-alias", server.split(":")[0]]
            else:
                command = ["sudo", "ip", "addr", "del", server.split(":")[0] + "/32", "dev", "lo"]

            proc = subprocess.Popen(["sudo", "-S"] + command,
                                    stdin=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    universal_newlines=True)
            proc.communicate(password + "\n")
            logger.info(f"executed: {command}")

    def _add_local_interfaces(self) -> None:
        """
        Add local network interfaces/aliases for the specified servers.

        Returns:
            None
        """
        password = getpass.getpass("please enter sudo password (possible plaintext display): ")
        for server in self._forwarder_servers:
            if sys.platform == "darwin":
                command = ["sudo", "ifconfig", "lo0", "alias", server.split(":")[0]]
            else:
                command = ["sudo", "ip", "addr", "add", server.split(":")[0] + "/32", "dev", "lo"]

            proc = subprocess.Popen(["sudo", "-S"] + command,
                                    stdin=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    universal_newlines=True)
            proc.communicate(password + "\n")
            logger.info(f"executed: {command}")

    def deactivate_forwarder(self) -> None:
        """
        Deactivate forwarder.

        Returns:
            None
        """
        self._remove_local_interfaces()
        self._disconnect_ssh_tunnel()

    def activate_forwarder(self) -> None:
        """
        Activate forwarder.

        Returns:
            None
        """
        self._add_local_interfaces()
        self._connect_ssh_tunnel()


if __name__ == "__main__":
    ForwarderSetting().activate_forwarder()
