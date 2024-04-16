# -*- coding: utf-8 -*-
from utils.clickhouse_connection import ClickhouseConnection
from utils.common import get_env_conf
from utils.driver_shell import DriverShell
from utils.mysql_connection import MysqlConnection
from utils.redis_connection import RedisConnection
from utils.tunnel_shell import TunnelShell


class Constants:
    _PORTAL_CONF = get_env_conf(name="portal")
    BASE_URL = _PORTAL_CONF["base_url"]
    HEADERS = _PORTAL_CONF["headers"]


class Global:
    CONSTANTS = Constants()
    TUNNEL = TunnelShell()
    DRIVER = DriverShell()
    DB = MysqlConnection()
    SR = RedisConnection()
    CK = ClickhouseConnection()
