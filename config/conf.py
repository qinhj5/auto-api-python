# -*- coding: utf-8 -*-
from utils.common import get_env_conf
from utils.tunnel_shell import TunnelShell
from utils.driver_shell import DriverShell
from utils.mysql_connection import MysqlConnection
from utils.redis_connection import RedisConnection
from utils.clickhouse_connection import ClickhouseConnection


class Constants:
    _PORTAL_CONF = get_env_conf(name="portal")
    BASE_URL = _PORTAL_CONF["base_url"]
    HEADERS = _PORTAL_CONF["headers"]


class Global:
    constants = Constants()
    tunnel = TunnelShell()
    driver = DriverShell()
    db = MysqlConnection()
    sr = RedisConnection()
    ck = ClickhouseConnection()
