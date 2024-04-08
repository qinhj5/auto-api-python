# -*- coding: utf-8 -*-
import os
import sys
import base64
import traceback
from email import encoders
from utils.dirs import tmp_dir
from utils.logger import logger
from types import TracebackType
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from utils.common import get_ext_conf
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

    def __init__(self, conf_name: str = "google_api") -> None:
        """
        Initialize an instance of the GoogleEmail class.

        Args:
            conf_name (str): The name of the configuration. Defaults to "google_api".

        Returns:
            None
        """
        self._conf = get_ext_conf(name=conf_name)
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
        Initialize the gmail_service.

        Returns:
            None
        """
        os.makedirs(tmp_dir, exist_ok=True)
        google_token_path = os.path.abspath(os.path.join(tmp_dir, "google_email_token.json"))
        credentials = None
        if os.path.exists(google_token_path):
            try:
                credentials = Credentials.from_authorized_user_file(
                    filename=google_token_path,
                    scopes=["https://www.googleapis.com/auth/gmail.send"]
                )
            except Exception as e:
                logger.error(f"{e}\n{traceback.format_exc()}")
                sys.exit(1)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    client_config=self._conf.get("client_config"),
                    scopes=["https://www.googleapis.com/auth/gmail.send"]
                )
                try:
                    credentials = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"{e}\n{traceback.format_exc()}")
                    sys.exit(1)
            with open(google_token_path, "w") as f:
                f.write(credentials.to_json())

        self._gmail_service = build("gmail", "v1", credentials=credentials)

    def send(self,
             subject: str,
             body: str,
             to_recipients: str,
             cc_recipients: str = None,
             bcc_recipients: str = None,
             attachment_path: str = None
             ) -> None:
        """
        Send an email using Gmail API.

        Args:
            subject (str): The email subject.
            body (str): The email body.
            to_recipients (str): Comma-separated email addresses of the primary recipients.
            cc_recipients (str): Comma-separated email addresses of the CC recipients. Default is None.
            bcc_recipients (str): Comma-separated email addresses of the BCC recipients. Default is None.
            attachment_path (str): Path to the file to be attached. Default is None (no attachment).

        Returns:
            None
        """
        message = MIMEMultipart()
        message["subject"] = subject
        message.attach(MIMEText(body, "plain"))

        recipients = to_recipients.split(",")
        recipients = [recipient for recipient in recipients if recipient]

        default_recipient = self._conf.get("google_email").get("default_recipient")
        if default_recipient:
            recipients.append(default_recipient)
        message["to"] = ",".join(recipients)

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
    # OAuth consent screen is required before using Gmail API
    GoogleEmail().send(to_recipients="", subject="", body="")
