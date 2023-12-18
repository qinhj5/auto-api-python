# -*- coding: utf-8 -*-
import pymysql
import threading
from pymysql import cursors
from utils import get_conf, singleton
from sshtunnel import SSHTunnelForwarder
from typing import Tuple, Any, Optional, List, Dict

pymysql.install_as_MySQLdb()


def create_mysql_connection(mysql_conf: dict, ssh_conf: dict = None, use_tunnel: bool = True) -> Tuple[Any, Any]:
    """
    Create a MySQL connection.

    Args:
        mysql_conf (dict): MySQL configuration information.
        ssh_conf (dict): SSH configuration information.
        use_tunnel (bool): Whether to use an SSH tunnel. Defaults to True.

    Returns:
        Tuple[Any, Any]: MySQL connection object and SSH tunnel object (if using an SSH tunnel).

    Raises:
        Exception: Raised when connection creation fails.
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


@singleton
class MysqlConnection:
    def __init__(self):
        """
        Initialize an instance of the MysqlConnection class.

        Returns:
            None
        """
        self.mysql_conf = get_conf(name="mysql")
        self.ssh_conf = get_conf(name="ssh")
        self.connection = None
        self.tunnel = None
        self._lock = threading.Lock()

    def _execute_sql(self, sql: str) -> Tuple[int, Any]:
        """
        Execute the SQL statement.

        Args:
            sql (str): SQL statement.

        Returns:
            Tuple[int, Any]: Number of affected rows and cursor object.
        """
        if self.connection is None:
            self.connection, self.tunnel = create_mysql_connection(mysql_conf=self.mysql_conf, ssh_conf=self.ssh_conf)
        with self.connection.cursor(cursors.DictCursor) as cursor:
            rows = cursor.execute(sql)
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
            self.connection.commit()

    def fetchone(self, sql: str) -> Optional[Dict]:
        """
        Fetch a single query result.

        Args:
            sql (str): SQL statement.

        Returns:
            Optional[Dict]: Query result in dictionary form. Returns None if the query result is empty.
        """
        with self._lock:
            rows, cursor = self._execute_sql(sql)
            return cursor.fetchone() if rows > 0 else None

    def fetchall(self, sql: str) -> Optional[List[Dict]]:
        """
        Fetch multiple query results.

        Args:
            sql (str): SQL statement.

        Returns:
            Optional[List[Dict]]: Query result in list form. Returns an empty list if the query result is empty.
        """
        with self._lock:
            rows, cursor = self._execute_sql(sql)
            return cursor.fetchall() if rows > 0 else []

    def close(self):
        """
        Close the database connection.

        Returns:
            None
        """
        with self._lock:
            if self.connection:
                self.connection.close()
            if self.tunnel:
                self.tunnel.close()
