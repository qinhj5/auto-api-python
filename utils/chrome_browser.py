# -*- coding: utf-8 -*-
import os
import sys
import json
import base64
import shutil
import sqlite3
import datetime
import traceback
from utils.dirs import tmp_dir
from utils.logger import logger
from utils.common import get_env_conf
from typing import Tuple, List, Dict, Any, Optional


class ChromeBrowser:
    def __init__(self, conf_name: str = "chrome_browser") -> None:
        """
       Initialize an instance of the ChromeBrowser class.

       Args:
           conf_name (str): The name of the configuration. Defaults to "chrome_browser".

       Returns:
           None
       """
        self._conf = get_env_conf(name=conf_name)
        self._host = self._conf.get("host")
        self._data_dir = self._conf.get("data_dir")
        self._cookies_path = ""
        self._local_state_path = ""
        self._leveldb_path = ""
        self._platform = sys.platform
        self._cookies = list()
        self._local_storage_items = list()
        self._init()

    def _init(self) -> None:
        """
        Initialization function to copy essential directory and files to the temporary directory.

        Returns:
           None
        """
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir, exist_ok=True)

        if self._platform == "darwin":
            sub_dir = "Default/Cookies"
        elif self._platform == "win32":
            sub_dir = "Default/Network/Cookies"
        else:
            logger.error("only support macOS and Windows")
            sys.exit(1)

        cookies_path = os.path.abspath(os.path.join(self._data_dir, sub_dir))
        if not os.path.exists(cookies_path):
            logger.error(f"cookies path ({cookies_path}) does not exist")
            sys.exit(1)
        else:
            self._cookies_path = os.path.abspath(os.path.join(tmp_dir, "Cookies"))
            if os.path.exists(self._cookies_path):
                os.remove(self._cookies_path)
            shutil.copy2(cookies_path, self._cookies_path)

        local_state_path = os.path.abspath(os.path.join(self._data_dir, "Local State"))
        if not os.path.exists(local_state_path):
            logger.error(f"local state path ({local_state_path}) does not exist")
            sys.exit(1)
        else:
            self._local_state_path = os.path.abspath(os.path.join(tmp_dir, "Local State"))
            if os.path.exists(self._local_state_path):
                os.remove(self._local_state_path)
            shutil.copy2(local_state_path, self._local_state_path)

        leveldb_path = os.path.abspath(os.path.join(self._data_dir, "Default/Local Storage/leveldb"))
        if not os.path.exists(leveldb_path):
            logger.error(f"leveldb path ({leveldb_path}) does not exist")
            sys.exit(1)
        else:
            self._leveldb_path = os.path.abspath(os.path.join(tmp_dir, "leveldb"))
            if os.path.exists(self._leveldb_path):
                shutil.rmtree(self._leveldb_path)
            shutil.copytree(leveldb_path, self._leveldb_path)

        self._fetch_browser_cookies()
        self._fetch_browser_local_storage_items()

    @staticmethod
    def _dict_factory(cursor: sqlite3.Cursor, row: Tuple[Any]) -> dict:
        """
        Convert a database row into a dictionary.

        Args:
            cursor (sqlite3.Cursor): The database cursor object.
            row (Tuple[Any]): The row of data retrieved from the database.

        Returns:
            dict: A dictionary representing the row of data.
        """
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]

        return d

    def _get_encryption_key(self) -> Optional[bytes]:
        """
        Retrieve the encryption key for decrypting Chrome cookies.

        Returns:
            Optional[bytes]: The encryption key as bytes, or None if the platform is not supported.
        """
        if self._platform == "darwin":
            import keyring  # pip install keyring==24.3.1
            password = keyring.get_password("Chrome Safe Storage", "Chrome")

            if isinstance(password, str):
                password = password.encode("utf8")

            from cryptography.hazmat.primitives.hashes import SHA1
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

            kdf = PBKDF2HMAC(
                algorithm=SHA1(),
                backend=default_backend(),
                iterations=1003,
                length=16,
                salt=b"saltysalt",
            )

            return kdf.derive(password)
        elif self._platform == "win32":
            try:
                with open(self._local_state_path, "r", encoding="utf-8") as f:
                    base64_encrypted_key = json.load(f)["os_crypt"]["encrypted_key"]
            except Exception as e:
                logger.error(f"{e}\n{traceback.format_exc()}")
                sys.exit(1)

            encrypted_key_with_header = base64.b64decode(base64_encrypted_key)
            encrypted_key = encrypted_key_with_header[5:]

            import win32crypt  # pip install pywin32==306
            return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        else:
            logger.error("only support macOS and Windows")
            sys.exit(1)

    @staticmethod
    def _clean_bytes(decrypted: bytes) -> str:
        """
        Clean up decrypted bytes and convert them to a string.

        Args:
            decrypted (bytes): The decrypted bytes to clean up.

        Returns:
            str: The cleaned up string.
        """
        if not decrypted:
            return ""

        last = decrypted[-1]
        return decrypted[:-last].decode("utf8")

    def _decrypt_cookie_value(self, encrypted_value: bytes) -> str:
        """
        Decrypt the encrypted cookie value.

        Args:
            encrypted_value (bytes): The encrypted cookie value.

        Returns:
            str: The decrypted cookie value.
        """
        encryption_key = self._get_encryption_key()

        if self._platform == "darwin":
            init_vector = b" " * 16
            encrypted_value = encrypted_value[3:]

            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.ciphers import Cipher
            from cryptography.hazmat.primitives.ciphers.modes import CBC
            from cryptography.hazmat.primitives.ciphers.algorithms import AES

            cipher = Cipher(algorithm=AES(encryption_key), mode=CBC(init_vector), backend=default_backend())
            de_cryptor = cipher.decryptor()
            decrypted = de_cryptor.update(encrypted_value) + de_cryptor.finalize()

            return ChromeBrowser._clean_bytes(decrypted)
        else:
            init_vector = encrypted_value[3:15]
            cipher_bytes = encrypted_value[15:]

            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            aes_gcm = AESGCM(encryption_key)
            plain_bytes = aes_gcm.decrypt(init_vector, cipher_bytes, None)

            return plain_bytes.decode("utf-8")

    @staticmethod
    def _is_expired(microseconds: int) -> bool:
        """
        Check if the expiration time has passed.

        Args:
            microseconds (int): The expiration time in microseconds.

        Returns:
            bool: True if the expiration time has passed, False otherwise.
        """
        expiration_timestamp = microseconds / 10 ** 6 - 11644473600
        expiration_datetime = datetime.datetime.fromtimestamp(expiration_timestamp)

        return expiration_datetime < datetime.datetime.now()

    def _fetch_browser_cookies(self) -> None:
        """
        Fetch browser cookies and store them in self._cookies

        Returns:
            None
        """
        conn = sqlite3.connect(self._cookies_path)
        conn.row_factory = ChromeBrowser._dict_factory
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT host_key, \
                            name, \
                            encrypted_value, \
                            expires_utc, \
                            has_expires, \
                            last_update_utc FROM cookies;")
            raw_cookies = cursor.fetchall()
        except Exception as e:
            logger.error(f"{e}\n{traceback.format_exc()}")
            sys.exit(1)
        else:
            for cookie in raw_cookies:
                last_update_time = datetime.datetime.fromtimestamp(cookie["last_update_utc"] / 10 ** 6 - 11644473600)
                self._cookies.append(
                    {"name": cookie["name"],
                     "value": self._decrypt_cookie_value(cookie["encrypted_value"]),
                     "host": cookie["host_key"],
                     "is_expired": ChromeBrowser._is_expired(cookie["expires_utc"]) if cookie["has_expires"] else False,
                     "update_time": last_update_time.strftime("%Y-%m-%d %H:%M:%S")}
                )
        finally:
            conn.close()

    def _fetch_browser_local_storage_items(self) -> None:
        """
        Fetch browser local storage items and store them in self._local_storage_items

        Returns:
            None
        """
        if self._platform == "darwin":
            import leveldb  # pip install leveldb==0.201
            try:
                db = leveldb.LevelDB(self._leveldb_path)
            except Exception as e:
                logger.error(f"{e}\n{traceback.format_exc()}")
                sys.exit(1)
            else:
                for k in db.RangeIter(include_value=False):
                    self._local_storage_items.append({"key": k, "value": db.Get(k)})
        elif self._platform == "win32":
            import plyvel  # pip install plyvel-win32==1.3.0
            try:
                db = plyvel.DB(self._leveldb_path, create_if_missing=False)
            except Exception as e:
                logger.error(f"{e}\n{traceback.format_exc()}")
                sys.exit(1)
            else:
                with db.iterator(include_value=False) as it:
                    for key in it:
                        self._local_storage_items.append({"key": key, "value": db.get(key)})
        else:
            logger.error("only support macOS and Windows")
            sys.exit(1)

    def get_all_cookies(self) -> List[Dict[str, Any]]:
        """
        Get a list of all cookies.

        Returns:
            List[Dict[str, Any]]: A list containing all cookies. Each cookie is represented as a dict.
        """
        if self._cookies:
            return self._cookies
        else:
            logger.warning("no local cookies")
            return []

    def get_all_local_storage_items(self) -> List[Dict[str, Any]]:
        """
        Get a list of all local storage items.

        Returns:
            List[Dict[str, Any]]: A list containing all local storage items. Each item is represented as a dict.
        """
        if self._local_storage_items:
            return self._local_storage_items
        else:
            logger.warning("no local local storage items")
            return []

    def get_cookie_value(self, name: str, host: str = None) -> str:
        """
        Get the value of a cookie.

        Args:
            name (str): The name of the cookie.
            host (str): The host of the cookie. If not provided, the default host will be used.

        Returns:
            str: The cookie value of the specific host.
        """
        if not host:
            host = self._host

        cookie_values = [cookie for cookie in self._cookies if cookie["host"] == host and cookie["name"] == name]

        if len(cookie_values) == 0:
            logger.error(f"no such cookie ({name}) for host ({host})")
            sys.exit(1)

        if all(not cookie["is_expired"] for cookie in cookie_values):
            cookie_strings = [f"""{cookie["name"]}={cookie["value"]}""" for cookie in cookie_values]
            return ";".join(cookie_strings)
        else:
            logger.error("cookie value expired")
            sys.exit(1)

    def get_local_storage_item_value(self, name: str, host: str = None) -> bytearray:
        """
        Get the value of a local storage item.

        Args:
            name (str): The name of the local storage item.
            host (str): The host of the local storage item. If not provided, the default host will be used.

        Returns:
            bytearray: The local storage item value of the specific host.
        """
        if not host:
            host = self._host

        item_values = []
        for item in self._local_storage_items:
            try:
                item["key"].decode("utf-8")
            except Exception as e:
                logger.warning(f"{e}\n{traceback.format_exc()}")
                logger.warning(f"""skip key: {item["key"]}""")
            else:
                if host in item["key"].decode("utf-8") and name in item["key"].decode("utf-8"):
                    item_values.append(item)

        if len(item_values) == 0:
            logger.error(f"no such local storage item ({name}) for host ({host})")
            sys.exit(1)

        if len(item_values) != 1:
            logger.error(f"too many local storage items ({name}) for host ({host})")
            sys.exit(1)

        return item_values[0].get("value", bytearray())

    @staticmethod
    def bytes_to_unicode(byte_array: bytearray) -> str:
        """
        Convert a bytearray to a Unicode string.

        Args:
            byte_array (bytearray): The bytearray to convert.

        Returns:
            str: The Unicode string representation of the bytearray.
        """
        sub_byte_array = byte_array[1:]
        raw_unicode_string = "".join(
            [r"\u{:02x}{:02x}".format(sub_byte_array[i + 1], sub_byte_array[i])
             for i in range(0, len(sub_byte_array), 2)]
        )
        unicode_string = raw_unicode_string.encode().decode("unicode_escape")
        return unicode_string


if __name__ == "__main__":
    cookies = ChromeBrowser().get_all_cookies()
    for c in cookies:
        logger.info(c)
