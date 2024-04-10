# -*- coding: utf-8 -*-
import os
import filelock
import pymysql
import traceback
from utils.logger import logger
from utils.dirs import lock_dir
from types import TracebackType
from utils.common import get_env_conf
from pymysql import cursors, Connection
from sshtunnel import SSHTunnelForwarder
from typing import Tuple, List, Dict, Union

pymysql.install_as_MySQLdb()


class MysqlConnection:
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

    def __init__(self, mysql_conf_name: str = "mysql", ssh_conf_name: str = "ssh", use_tunnel: bool = True) -> None:
        """
        Initialize an instance of the MysqlConnection class.

        Args:
            mysql_conf_name (str): The name of the MySQL configuration. Defaults to "mysql".
            ssh_conf_name (str): The name of the SSH configuration. Defaults to "ssh".
            use_tunnel (bool): Whether to use an SSH tunnel. Defaults to True.

        Returns:
            None
        """
        self._lock = filelock.FileLock(os.path.abspath(os.path.join(lock_dir, f"{mysql_conf_name}.lock")))
        self._mysql_conf = get_env_conf(name=mysql_conf_name)
        self._ssh_conf = get_env_conf(name=ssh_conf_name)
        self._connection = None
        self._use_tunnel = use_tunnel
        self._tunnel_forwarder = None

    def __enter__(self) -> 'MysqlConnection':
        """
        Context manager method for entering the context.

        Returns:
            MysqlConnection: The current instance of the MysqlConnection class.
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
            logger.error(f"""{exc_val}\n{"".join(traceback.format_tb(exc_tb))}""")

        self.close()

    @staticmethod
    def _create_mysql_connection(mysql_conf: dict,
                                 ssh_conf: dict,
                                 use_tunnel: bool) -> Union[Tuple[None, Connection],
                                                            Tuple[SSHTunnelForwarder, Connection]]:
        """
        Create a MySQL connection.

        Args:
            mysql_conf (dict): MySQL configuration information.
            ssh_conf (dict): SSH configuration information.
            use_tunnel (bool): Whether to use an SSH tunnel.

        Returns:
            Union[Tuple[None, Connection], Tuple[SSHTunnelForwarder, Connection]]: A tuple containing the SSH tunnel
            and MySQL connection objects if using tunnel, otherwise None and MySQL connection object.
        """
        if use_tunnel:
            tunnel_forwarder = SSHTunnelForwarder(
                ssh_address=(ssh_conf["ssh_host"], ssh_conf["ssh_port"]),
                ssh_username=ssh_conf["ssh_user"],
                ssh_pkey=ssh_conf.get("ssh_key"),
                ssh_password=ssh_conf.get("ssh_password"),
                remote_bind_address=(mysql_conf["host"], mysql_conf["port"])
            )
            tunnel_forwarder.start()

            connection = pymysql.connect(
                host="localhost",
                port=tunnel_forwarder.local_bind_port,
                user=mysql_conf["user"],
                password=mysql_conf["password"],
                database=mysql_conf["database"]
            )
            return tunnel_forwarder, connection
        else:
            connection = pymysql.connect(
                host=mysql_conf["host"],
                port=mysql_conf["port"],
                user=mysql_conf["user"],
                password=mysql_conf["password"],
                database=mysql_conf["database"],
            )
            return None, connection

    def _execute_sql(self, sql: str) -> Tuple[int, cursors.DictCursor]:
        """
        Execute the SQL statement.

        Args:
            sql (str): SQL statement.

        Returns:
            Tuple[int, cursors.DictCursor]: Number of affected rows and cursor object.
        """
        try:
            if self._connection is None:
                self.close()
                self._tunnel_forwarder, self._connection = MysqlConnection._create_mysql_connection(self._mysql_conf,
                                                                                                    self._ssh_conf,
                                                                                                    self._use_tunnel)
        except Exception as e:
            logger.error(f"{e}\n{traceback.format_exc()}")
            self.close()
        else:
            with self._connection.cursor(cursors.DictCursor) as cursor:
                rows = cursor.execute(sql)
                logger.info(f"executed sql: {sql}")
                return rows, cursor

    def execute(self, sql: str) -> None:
        """
        Execute the SQL statement.

        Args:
            sql (str): SQL statement.

        Returns:
            None
        """
        with self._lock:
            self._execute_sql(sql)
            self._connection.commit()

    def fetchone(self, sql: str) -> Dict:
        """
        Fetch a single query result.

        Args:
            sql (str): SQL statement.

        Returns:
            Dict: Query result in dictionary form. Returns None if the query result is empty.
        """
        rows, cursor = self._execute_sql(sql)
        return cursor.fetchone() if rows > 0 else None

    def fetchall(self, sql: str) -> List[Dict]:
        """
        Fetch multiple query results.

        Args:
            sql (str): SQL statement.

        Returns:
            List[Dict]: Query result in list form. Returns an empty list if the query result is empty.
        """
        rows, cursor = self._execute_sql(sql)
        return cursor.fetchall() if rows > 0 else []

    def close(self) -> None:
        """
        Close the MySQL connection.

        Returns:
            None
        """
        if self._connection:
            self._connection.close()
        if self._tunnel_forwarder:
            self._tunnel_forwarder.stop()
