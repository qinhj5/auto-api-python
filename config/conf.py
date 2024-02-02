# -*- coding: utf-8 -*-
from utils.common import get_conf
from utils.ssh_tunnel import SSHTunnel
from utils.driver_client import DriverClient
from utils.mysql_connection import MysqlConnection
from utils.redis_connection import RedisConnection
from utils.clickhouse_connection import ClickhouseConnection


class Constants:
    _PORTAL_CONF = get_conf(name="portal")
    BASE_URL = _PORTAL_CONF["base_url"]
    HEADERS = _PORTAL_CONF["headers"]


class Global:
    constants = Constants()
    tunnel = SSHTunnel()
    driver = DriverClient()
    db = MysqlConnection()
    sr = RedisConnection()
    ck = ClickhouseConnection()
