# -*- coding: utf-8 -*-
import os
import traceback
from types import TracebackType
from typing import Tuple, Union

import filelock
from redis import StrictRedis
from sshtunnel import SSHTunnelForwarder

from utils.common import get_env_conf
from utils.dirs import lock_dir
from utils.logger import logger


class RedisConnection:
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
        self,
        redis_conf_name: str = "redis",
        ssh_conf_name: str = "ssh",
        use_tunnel: bool = True,
    ) -> None:
        """
        Initialize an instance of the RedisConnection class.

        Args:
            redis_conf_name (str): The name of the Redis configuration. Defaults to "redis".
            ssh_conf_name (str): The name of the SSH configuration. Defaults to "ssh".
            use_tunnel (bool): Whether to use an SSH tunnel. Defaults to True.

        Returns:
            None
        """
        self._lock = filelock.FileLock(
            os.path.abspath(os.path.join(lock_dir, f"{redis_conf_name}.lock"))
        )
        self._redis_conf = get_env_conf(name=redis_conf_name)
        self._ssh_conf = get_env_conf(name=ssh_conf_name)
        self._connection = None
        self._use_tunnel = use_tunnel
        self._tunnel_forwarder = None

    def __enter__(self) -> "RedisConnection":
        """
        Context manager method for entering the context.

        Returns:
            RedisConnection: The current instance of the RedisConnection class.
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
    def _create_redis_connection(
        redis_conf: dict, ssh_conf: dict, use_tunnel: bool
    ) -> Union[Tuple[None, StrictRedis], Tuple[SSHTunnelForwarder, StrictRedis]]:
        """
        Create a Redis connection.

        Args:
            redis_conf (dict): Redis configuration information.
            ssh_conf (dict): SSH configuration information.
            use_tunnel (bool): Whether to use an SSH tunnel.

        Returns:
            Union[Tuple[None, StrictRedis], Tuple[SSHTunnelForwarder, StrictRedis]]: A tuple containing the SSH tunnel
            and Redis connection objects if using tunnel, otherwise None and Redis connection object.
        """
        if use_tunnel:
            tunnel_forwarder = SSHTunnelForwarder(
                ssh_address=(ssh_conf["ssh_host"], ssh_conf["ssh_port"]),
                ssh_username=ssh_conf["ssh_user"],
                ssh_pkey=ssh_conf.get("ssh_key"),
                ssh_password=ssh_conf.get("ssh_password"),
                remote_bind_address=(redis_conf["host"], redis_conf["port"]),
            )
            tunnel_forwarder.start()

            connection = StrictRedis(
                host="localhost",
                port=tunnel_forwarder.local_bind_port,
                password=redis_conf["password"],
                db=redis_conf["db"],
            )
            return tunnel_forwarder, connection
        else:
            connection = StrictRedis(
                host=redis_conf["host"],
                port=redis_conf["port"],
                password=redis_conf["password"],
                db=redis_conf["db"],
            )
            return None, connection

    def _check_connection(self) -> None:
        """
        Check whether the connection is valid.

        Returns:
            None
        """
        try:
            if self._connection is None:
                self.close()
                (
                    self._tunnel_forwarder,
                    self._connection,
                ) = RedisConnection._create_redis_connection(
                    self._redis_conf, self._ssh_conf, self._use_tunnel
                )
        except Exception as exception:
            logger.error(f"{exception}\n{traceback.format_exc()}")
            self.close()

    def set(self, name: str, value: str) -> None:
        """
        Set the value of a specified key.

        Args:
            name (str): The name of the key.
            value (str): The value to be set.

        Returns:
            None

        """
        self._check_connection()
        with self._lock:
            self._connection.set(name, value)

    def get(self, name: str) -> str:
        """
        Retrieve the value of a specified key.

        Args:
            name (str): The name of the key.

        Returns:
            str: The value of the key.
        """
        self._check_connection()
        return self._connection.get(name).decode("utf-8")

    def hset(self, name: str, key: str, value: str) -> None:
        """
        Set the value of a specified field in a hash.

        Args:
            name (str): The name of the hash.
            key (str): The field key.
            value (str): The value to be set.

        Returns:
            None

        """
        self._check_connection()
        with self._lock:
            self._connection.hset(name, key, value)

    def hget(self, name: str, key: str) -> str:
        """
        Get the value of a specified field in a hash.

        Args:
            name (str): The name of the hash.
            key (str): The field key.

        Returns:
            str: The value of the field.

        """
        self._check_connection()
        return self._connection.hget(name, key).decode("utf-8")

    def close(self) -> None:
        """
        Close the Redis connection.

        Returns:
            None
        """
        if self._connection:
            self._connection.close()
        if self._tunnel_forwarder:
            self._tunnel_forwarder.close()
