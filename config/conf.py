# -*- coding: utf-8 -*-
from utils import get_conf, SSHTunnel, MysqlConnection


class Constants:
    _PORTAL_CONF = get_conf(name="portal")
    BASE_URL = _PORTAL_CONF["base_url"]
    HEADERS = _PORTAL_CONF["headers"]


class Global:
    constants = Constants()
    tunnel = SSHTunnel()
    db = MysqlConnection()
