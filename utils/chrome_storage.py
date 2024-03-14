# -*- coding: utf-8 -*-
import os
import sys
import json
import base64
import sqlite3
import datetime
import traceback
from utils.logger import logger
from utils.common import get_env_conf
from typing import Tuple, List, Dict, Any, Optional


class ChromeStorage:
    def __init__(self, conf_name: str = "chrome_storage") -> None:
        """
       Initialize an instance of the ChromeStorage class.

       Args:
           conf_name (str): The name of the ChromeStorage configuration. Defaults to "chrome_storage".

       Returns:
           None
       """
        self._conf = get_env_conf(name=conf_name)
        self._host = self._conf.get("host")
        self._cookie_file = self._conf.get("cookie_file")
        self._local_state = self._conf.get("local_state")
        self._platform = sys.platform
        self._cookies = list()

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
            import keyring
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
                with open(self._local_state, "r", encoding="utf-8") as f:
                    base64_encrypted_key = json.load(f)["os_crypt"]["encrypted_key"]
            except Exception as e:
                logger.error(f"{e}\n{traceback.format_exc()}")
                sys.exit(1)
                
            encrypted_key_with_header = base64.b64decode(base64_encrypted_key)
            encrypted_key = encrypted_key_with_header[5:]
            
            import win32crypt

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

            return ChromeStorage._clean_bytes(decrypted)
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
        if not os.path.exists(self._cookie_file):
            logger.error(f"path ({self._cookie_file}) does not exist")
            sys.exit(1)

        conn = sqlite3.connect(self._cookie_file)
        conn.row_factory = ChromeStorage._dict_factory
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
        else:
            for cookie in raw_cookies:
                last_update_time = datetime.datetime.fromtimestamp(cookie["last_update_utc"] / 10 ** 6 - 11644473600)
                self._cookies.append(
                    {"name": cookie["name"],
                     "value": self._decrypt_cookie_value(cookie["encrypted_value"]),
                     "host": cookie["host_key"],
                     "is_expired": ChromeStorage._is_expired(cookie["expires_utc"]) if cookie["has_expires"] else False,
                     "update_time": last_update_time.strftime("%Y-%m-%d %H:%M:%S")}
                )
        finally:
            conn.close()

    def get_all_cookies(self) -> List[Dict[str, Any]]:
        """
        Get a list of all cookies.

        Returns:
            List[Dict[str, Any]]: A list containing all cookies. Each cookie is represented as a dict.
        """
        self._fetch_browser_cookies()

        if self._cookies:
            return self._cookies
        else:
            logger.warning("no local cookies")
            return []

    def get_cookie_value(self, name: str, host: str = None) -> str:
        """
        Get the value of a cookie.

        Args:
            name (str): The name of the cookie.
            host (str): The host of the cookie. If not provided, the default host will be used.

        Returns:
            str: The cookie value of host.
        """
        self._fetch_browser_cookies()

        if not host:
            host = self._host

        cookie_values = [cookie for cookie in self._cookies if cookie["host"] == host and cookie["name"] == name]
        if len(cookie_values) == 0:
            logger.warning(f"no such cookie ({name}) for host ({self._host})")
            return ""

        if all(not cookie["is_expired"] for cookie in cookie_values):
            cookie_strings = [f"""{cookie["name"]}={cookie["value"]}""" for cookie in cookie_values]
            return ";".join(cookie_strings)
        else:
            logger.error("cookie value expired")
            return ""


if __name__ == "__main__":
    cookies = ChromeStorage().get_all_cookies()
    for c in cookies:
        logger.info(c)
