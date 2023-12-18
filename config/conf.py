# -*- coding: utf-8 -*-
from utils import get_conf
from connection.mysql_connection import MysqlConnection


class Constants:
    _CONF = get_conf(name="portal")
    BASE_URL = _CONF["base_url"]
    HEADERS = _CONF["headers"]


class Global:
    constants = Constants()
    db = MysqlConnection()
