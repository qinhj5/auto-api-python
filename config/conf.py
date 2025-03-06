# -*- coding: utf-8 -*-
from utils.clickhouse_connection import ClickhouseConnection
from utils.common import get_env_conf
from utils.driver_shell import DriverShell
from utils.lazy_loader import LazyLoader
from utils.mysql_connection import MysqlConnection
from utils.redis_connection import RedisConnection
from utils.tunnel_shell import TunnelShell


class Constants:
    _PORTAL_CONF = get_env_conf(name="portal")
    BASE_URL = _PORTAL_CONF.get("base_url")
    HEADERS = _PORTAL_CONF.get("headers")


class Global:
    CONSTANTS = Constants()
    TUNNEL = LazyLoader(lambda: TunnelShell())
    DRIVER = LazyLoader(lambda: DriverShell())
    DB = LazyLoader(lambda: MysqlConnection())
    SR = LazyLoader(lambda: RedisConnection())
    CK = LazyLoader(lambda: ClickhouseConnection())
