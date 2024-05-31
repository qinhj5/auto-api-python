# -*- coding: utf-8 -*-
import binascii
import os
import traceback

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

from utils.dirs import config_dir, tmp_dir
from utils.logger import logger


def encrypt_file(plaintext_file_path: str, encrypted_file_path: str, key: str) -> None:
    """
    Encrypts a plaintext file using AES-128-CBC encryption.

    Args:
        plaintext_file_path (str): The path to the plaintext file to be encrypted.
        encrypted_file_path (str): The path to the encrypted file.
        key (str): The hexadecimal representation of the 16-byte encryption key.

    Returns:
        None
    """
    with open(plaintext_file_path, "rb") as plaintext_f:
        plaintext = plaintext_f.read()

    cipher = AES.new(binascii.unhexlify(key.encode("utf-8")), AES.MODE_CBC)
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

    with open(encrypted_file_path, "wb") as encrypted_f:
        encrypted_f.write(cipher.iv)
        encrypted_f.write(ciphertext)


def decrypt_file(encrypted_file_path: str, decrypted_file_path: str, key: str) -> None:
    """
    Decrypts an encrypted file using AES-128-CBC decryption.

    Args:
        encrypted_file_path (str): The path to the encrypted file.
        decrypted_file_path (str): The path to the decrypted file.
        key (str): The hexadecimal representation of the 16-byte encryption key.

    Returns:
        None
    """
    with open(encrypted_file_path, "rb") as encrypted_f:
        iv = encrypted_f.read(16)
        ciphertext = encrypted_f.read()

    cipher = AES.new(binascii.unhexlify(key.encode("utf-8")), AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)

    with open(decrypted_file_path, "wb") as decrypted_f:
        decrypted_f.write(plaintext)


def encrypt_config() -> None:
    """
    Encrypts all YAML and JSON configuration files in the config_dir directory.

    The function generates a random 256-bit encryption key, saves it to a file in the tmp_dir directory,
    and then encrypts each configuration file using the AES-256-CBC algorithm and the generated key.
    The encrypted files are saved with the ".encrypted" extension in the same directory as the original files.
    """
    key_str = binascii.hexlify(get_random_bytes(32)).decode("utf-8")
    os.makedirs(tmp_dir, exist_ok=True)

    key_path = os.path.abspath(os.path.join(tmp_dir, "key"))
    with open(key_path, "w", encoding="utf-8") as f:
        f.write(key_str)
    logger.info(f"key is saved to {key_path}")

    for root, dirs, files in os.walk(config_dir):
        for file in files:
            if file.endswith(".yaml") or file.endswith(".json"):
                file_path = os.path.abspath(os.path.join(root, file))
                encrypt_file(
                    plaintext_file_path=file_path,
                    encrypted_file_path=file_path + ".encrypted",
                    key=key_str,
                )


def decrypt_config() -> None:
    """
    Decrypts all encrypted configuration files in the config_dir directory.

    The function reads the encryption key from the environment variable "KEY" and then decrypts each
    encrypted configuration file using the AES-256-CBC algorithm and the key. The decrypted files are
    saved with the ".decrypted" extension in the same directory as the encrypted files.
    """
    logger.info("using key to decrypt config files")
    key_str = os.environ.get("KEY")
    os.makedirs(tmp_dir, exist_ok=True)

    for root, dirs, files in os.walk(config_dir):
        for file in files:
            if file.endswith(".yaml") or file.endswith(".json"):
                file_path = os.path.abspath(os.path.join(root, file))
                decrypt_file(
                    encrypted_file_path=file_path + ".encrypted",
                    decrypted_file_path=file_path + ".decrypted",
                    key=key_str,
                )


if __name__ == "__main__":
    try:
        encrypt_config()
    except Exception as e:
        logger.error(f"{e}\n{traceback.format_exc()}")
