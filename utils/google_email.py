# -*- coding: utf-8 -*-
import os
import base64
import traceback
from email import encoders
from utils.dirs import tmp_dir
from utils.logger import logger
from types import TracebackType
from utils.common import get_conf
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


class GoogleEmail:
    _instance = None

    def __new__(cls, *args, **kwargs) -> None:
        """
        Implement singleton mode.

        Returns:
            None
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, google_conf_name: str = "google_api") -> None:
        """
        Initialize an instance of the GoogleEmail class.

        Args:
            google_conf_name (str): The name of the GoogleEmail configuration. Defaults to "google_api".

        Returns:
            None
        """
        self._google_conf = get_conf(name=google_conf_name)
        self._credentials = None
        self._gmail_service = None
        self._init()

    def __enter__(self) -> 'GoogleEmail':
        """
        Context manager method for entering the context.

        Returns:
            GoogleEmail: The current instance of the GoogleEmail class.
        """
        return self

    def __exit__(self, exc_type: type, exc_val: BaseException, exc_tb: TracebackType) -> None:
        """
        Context manager method for exiting the context.

        Args:
            exc_type (type): The type of the exception (if any) that occurred within the context.
            exc_val (BaseException): The exception object (if any) that occurred within the context.
            exc_tb (TracebackType): The traceback object (if any) associated with the exception.

        Returns:
            None
        """
        if exc_type:
            logger.error(f"an exception of type {exc_type} occurred: {exc_val}")

        if exc_tb:
            logger.error("".join(traceback.format_tb(exc_tb)))

    def _init(self) -> None:
        """
        Initialize the credentials and gmail_service.

        Returns:
            None
        """
        self._credentials = None
        os.makedirs(tmp_dir, exist_ok=True)
        google_token_path = os.path.abspath(os.path.join(tmp_dir, "google_email_token.json"))
        if os.path.exists(google_token_path):
            self._credentials = Credentials.from_authorized_user_file(
                filename=google_token_path,
                scopes=["https://www.googleapis.com/auth/gmail.send"]
            )

        if not self._credentials or not self._credentials.valid:
            if self._credentials and self._credentials.expired and self._credentials.refresh_token:
                self._credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    client_config=self._google_conf.get("client_config"),
                    scopes=["https://www.googleapis.com/auth/gmail.send"]
                )
                self._credentials = flow.run_local_server(port=0)
            with open(google_token_path, "w") as f:
                f.write(self._credentials.to_json())

        self._gmail_service = build("gmail", "v1", credentials=self._credentials)

    def send(self,
             to_recipients: str,
             subject: str,
             body: str,
             cc_recipients: str = None,
             bcc_recipients: str = None,
             attachment_path: str = None
             ) -> None:
        """
        Send an email using Gmail API.

        Args:
            to_recipients (str): Comma-separated email addresses of the primary recipients.
            subject (str): The email subject.
            body (str): The email body.
            cc_recipients (str): Comma-separated email addresses of the CC recipients. Default is None.
            bcc_recipients (str): Comma-separated email addresses of the BCC recipients. Default is None.
            attachment_path (str): Path to the file to be attached. Default is None (no attachment).

        Returns:
            None
        """
        message = MIMEMultipart()
        message["to"] = to_recipients
        message["subject"] = subject
        message.attach(MIMEText(body, "plain"))

        if cc_recipients:
            message["cc"] = cc_recipients
        if bcc_recipients:
            message["bcc"] = bcc_recipients

        if attachment_path:
            attachment_name = os.path.basename(attachment_path)
            attachment = MIMEBase("application", "octet-stream")
            with open(attachment_path, "rb") as f:
                attachment.set_payload(f.read())
            encoders.encode_base64(attachment)
            attachment.add_header("Content-Disposition", f"attachment; filename={attachment_name}")
            message.attach(attachment)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        response = self._gmail_service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        logger.info(f"Email sent successfully! Response: {response}")


if __name__ == "__main__":
    GoogleEmail().send(to_recipients="", subject="", body="")
