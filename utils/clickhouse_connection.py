# -*- coding: utf-8 -*-
import os
import filelock
import traceback
from utils.logger import logger
from utils.dirs import lock_dir
from types import TracebackType
from utils.common import get_conf
from clickhouse_driver import Client
from sshtunnel import SSHTunnelForwarder
from typing import Union, Tuple, Any, List, Dict


class ClickhouseConnection:
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

    def __init__(self,
                 clickhouse_conf_name: str = "clickhouse",
                 ssh_conf_name: str = "ssh",
                 use_tunnel: bool = True) -> None:
        """
        Initialize an instance of the ClickhouseConnection class.

        Args:
            clickhouse_conf_name (str): The name of the ClickHouse configuration. Defaults to "clickhouse".
            ssh_conf_name (str): The name of the SSH configuration. Defaults to "ssh".
            use_tunnel (bool): Whether to use an SSH tunnel. Defaults to True.

        Returns:
            None
        """
        self._lock = filelock.FileLock(os.path.abspath(os.path.join(lock_dir, f"{clickhouse_conf_name}.lock")))
        self._clickhouse_conf = get_conf(name=clickhouse_conf_name)
        self._ssh_conf = get_conf(name=ssh_conf_name)
        self._connection = None
        self._use_tunnel = use_tunnel
        self._tunnel_forwarder = None

    def __enter__(self) -> 'ClickhouseConnection':
        """
        Context manager method for entering the context.

        Returns:
            ClickhouseConnection: The current instance of the ClickhouseConnection class.
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
    def _create_clickhouse_connection(clickhouse_conf: dict,
                                      ssh_conf: dict,
                                      use_tunnel: bool) -> Union[Tuple[None, Client],
                                                                 Tuple[SSHTunnelForwarder, Client]]:
        """
        Create a ClickHouse connection.

        Args:
            clickhouse_conf (dict): ClickHouse configuration information.
            ssh_conf (dict): SSH configuration information.
            use_tunnel (bool): Whether to use an SSH tunnel.

        Returns:
            Union[Tuple[None, Client], Tuple[SSHTunnelForwarder, Client]]: A tuple containing the SSH tunnel
            and ClickHouse connection objects if using tunnel, otherwise None and ClickHouse connection object.
        """
        if use_tunnel:
            tunnel_forwarder = SSHTunnelForwarder(
                ssh_address=(ssh_conf["ssh_host"], ssh_conf["ssh_port"]),
                ssh_username=ssh_conf["ssh_user"],
                ssh_pkey=ssh_conf.get("ssh_key"),
                ssh_password=ssh_conf.get("ssh_password"),
                remote_bind_address=(clickhouse_conf["host"], clickhouse_conf["port"])
            )
            tunnel_forwarder.start()

            connection = Client(
                host="localhost",
                port=tunnel_forwarder.local_bind_port,
                user=clickhouse_conf["user"],
                password=clickhouse_conf["password"],
                database=clickhouse_conf["database"]
            )
            return tunnel_forwarder, connection
        else:
            connection = Client(
                host=clickhouse_conf["host"],
                port=clickhouse_conf["port"],
                user=clickhouse_conf["user"],
                password=clickhouse_conf["password"],
                database=clickhouse_conf["database"],
            )
            return None, connection

    def _check_connection(self) -> None:
        """
        Check whether the connection is valid.

        Returns:
            None
        """
        try:
            if self._connection is None or not self._connection.ping():
                self.close()
                self._tunnel_forwarder, self._connection = ClickhouseConnection._create_clickhouse_connection(
                                                                                self._clickhouse_conf,
                                                                                self._ssh_conf,
                                                                                self._use_tunnel)
        except Exception as e:
            logger.error(f"{e}\n{traceback.format_exc()}")
            self.close()

    def execute(self, sql: str, params: dict = None) -> List[Dict[str, Any]]:
        """
        Execute an SQL query with optional parameters.

        Args:
            sql (str): The SQL query to execute.
            params (Dict[str, Any]): Optional parameters to be used in the query. Defaults to None.

        Returns:
            List[Dict[str, Any]]: The result of the query execution.
        """
        self._check_connection()
        data = self._connection.execute(sql, params, with_column_types=True)
        rows = data[0]
        columns = data[-1]
        return [dict(zip([col[0] for col in columns], row)) for row in rows]

    def insert(self, sql: str, data: list, columns: list) -> None:
        """
        Execute an insert query with data.

        Args:
            sql (str): The SQL insert query.
            data (list): The data to be inserted.
            columns (list): The specific columns to insert.

        Returns:
            None
        """
        self._check_connection()
        with self._lock:
            self._connection.insert(sql, data, columns)

    def close(self) -> None:
        """
        Close the ClickHouse connection.

        Returns:
            None
        """
        if self._connection:
            self._connection.disconnect()
        if self._tunnel_forwarder:
            self._tunnel_forwarder.stop()
