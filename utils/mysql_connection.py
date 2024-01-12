# -*- coding: utf-8 -*-
import pymysql
import threading
from utils import get_conf, logger
from pymysql import cursors, Connection
from sshtunnel import SSHTunnelForwarder
from typing import Tuple, Any, List, Dict, Optional

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
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        """
        Initialize an instance of the MysqlConnection class.

        Returns:
            None
        """
        self._mysql_conf = get_conf(name="mysql")
        self._ssh_conf = get_conf(name="ssh")
        self._connection = None
        self._tunnel = None
        self._lock = threading.Lock()

    @staticmethod
    def _create_mysql_connection(mysql_conf: dict,
                                 ssh_conf: dict = None,
                                 use_tunnel: bool = True) -> Tuple[Connection, Optional[SSHTunnelForwarder]]:
        """
        Create a MySQL connection.

        Args:
            mysql_conf (dict): MySQL configuration information.
            ssh_conf (dict): SSH configuration information.
            use_tunnel (bool): Whether to use an SSH tunnel. Defaults to True.

        Returns:
            Tuple[Connection, Optional[SSHTunnelForwarder]]: MySQL connection object and/or SSH tunnel object.
        """
        if use_tunnel:
            tunnel = SSHTunnelForwarder(
                ssh_address=(ssh_conf["ssh_host"], ssh_conf["ssh_port"]),
                ssh_username=ssh_conf["ssh_user"],
                ssh_pkey=ssh_conf.get("ssh_key"),
                ssh_password=ssh_conf.get("ssh_password"),
                remote_bind_address=(mysql_conf["host"], mysql_conf["port"])
            )
            tunnel.start()

            connection = pymysql.connect(
                host="localhost",
                port=tunnel.local_bind_port,
                user=mysql_conf["user"],
                password=mysql_conf["password"],
                database=mysql_conf["database"]
            )
            return connection, tunnel
        else:
            connection = pymysql.connect(
                host=mysql_conf["host"],
                port=mysql_conf["port"],
                user=mysql_conf["user"],
                password=mysql_conf["password"],
                database=mysql_conf["database"],
            )
            return connection, None

    def _execute_sql(self, sql: str) -> Tuple[int, cursors.DictCursor]:
        """
        Execute the SQL statement.

        Args:
            sql (str): SQL statement.

        Returns:
            Tuple[int, cursors.DictCursor]: Number of affected rows and cursor object.
        """
        if self._connection is None:
            self._connection, self._tunnel = MysqlConnection._create_mysql_connection(mysql_conf=self._mysql_conf,
                                                                                      ssh_conf=self._ssh_conf)
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
        with self._lock:
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
        with self._lock:
            rows, cursor = self._execute_sql(sql)
            return cursor.fetchall() if rows > 0 else []

    def close(self) -> None:
        """
        Close the database connection.

        Returns:
            None
        """
        with self._lock:
            if self._connection:
                self._connection.close()
            if self._tunnel:
                self._tunnel.close()
