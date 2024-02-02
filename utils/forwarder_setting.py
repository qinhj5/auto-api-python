# -*- coding: utf-8 -*-
import sys
import getpass
import subprocess
from utils.logger import logger
from utils.common import get_conf


def connect_ssh_tunnel(servers: list) -> None:
    """
    Connect to a jump host and establish SSH tunnels to the specified servers.

    Args:
        servers (list): List of servers in the format "<server>:<port>".

    Returns:
        None
    """
    forwards = []
    for server in servers:
        forwards += ["-L", f"{server}:{server}"]

    ssh_conf = get_conf("ssh")
    command = ["ssh"] + forwards + ["-N", "-f", f"""{ssh_conf.get("ssh_user")}@{ssh_conf.get("ssh_host")}"""]

    subprocess.call(command)
    logger.info(f"executed command: {command}")


def remove_local_interfaces(servers: str) -> None:
    """
    Remove local network interfaces/aliases for the specified servers.

    Args:
        servers (list): List of servers in the format "<server>:<port>".

    Returns:
        None
    """
    password = getpass.getpass("please enter sudo password (possible plaintext display): ")
    for server in servers:
        if sys.platform == "darwin":
            command = ["sudo", "ifconfig", "lo0", "-alias", server.split(":")[0]]
        else:
            command = ["sudo", "ip", "addr", "del", server.split(":")[0] + "/32", "dev", "lo"]

        proc = subprocess.Popen(["sudo", "-S"] + command,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                universal_newlines=True)
        proc.communicate(password + "\n")
        logger.info(f"executed command: {command}")


def add_local_interfaces(servers: str) -> None:
    """
    Add local network interfaces/aliases for the specified servers.

    Args:
        servers (list): List of servers in the format "<server>:<port>".

    Returns:
        None
    """
    password = getpass.getpass("please enter sudo password (possible plaintext display): ")
    for server in servers:
        if sys.platform == "darwin":
            command = ["sudo", "ifconfig", "lo0", "alias", server.split(":")[0]]
        else:
            command = ["sudo", "ip", "addr", "add", server.split(":")[0] + "/32", "dev", "lo"]

        proc = subprocess.Popen(["sudo", "-S"] + command,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                universal_newlines=True)
        proc.communicate(password + "\n")
        logger.info(f"executed command: {command}")


def activate_forwarder() -> None:
    """
    Connect the specified servers via ssh tunnel.

    Returns:
        None
    """
    servers = get_conf("forwarder").get("servers")
    add_local_interfaces(servers)
    connect_ssh_tunnel(servers)


def deactivate_forwarder() -> None:
    """
    Disconnect the specified servers via ssh tunnel.

    Returns:
        None
    """
    servers = get_conf("forwarder").get("servers")
    remove_local_interfaces(servers)


if __name__ == "__main__":
    activate_forwarder()
