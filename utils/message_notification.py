# -*- coding: utf-8 -*-
import traceback
from twilio.rest import Client
from utils.logger import logger
from utils.common import get_ext_conf


class MessageNotification:
    def __init__(self, conf_name: str = "message") -> None:
        """
        Initialize an instance of the MessageNotification class.

        Args:
            conf_name (str): The name of the configuration. Defaults to "message".

        Returns:
            None
        """
        self._conf = get_ext_conf(name=conf_name)
        self._account_sid = self._conf.get("account_sid")
        self._auth_token = self._conf.get("auth_token")
        self._from = self._conf.get("from")
        self._to = self._conf.get("to")

    def send_message(self, body: str = "Test finished") -> None:
        """
        Send a message to specified receiver.

        Args:
            body (str): The message that will be sent. Defaults to "Test finished".

        Returns:
            None
        """
        message = Client(self._conf.get("account_sid"), self._conf.get("auth_token")).messages.create(
            body=body,
            from_=self._from,
            to=self._to
        )

        logger.info(f"message sid: {message.sid}")


def send_message():
    MessageNotification().send_message()


if __name__ == "__main__":
    try:
        # refer to https://www.twilio.com
        send_message()
    except Exception as e:
        logger.error(f"{e}\n{traceback.format_exc()}")
