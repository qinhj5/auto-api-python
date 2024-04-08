# -*- coding: utf-8 -*-
import os
import time
import zipfile
import smtplib
import traceback
from utils.logger import logger
from email.mime.text import MIMEText
from utils.common import get_ext_conf
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from utils.dirs import report_dir, log_dir, log_summary_dir


class EmailNotification:
    def __init__(self, conf_name: str = "email") -> None:
        """
        Initialize an instance of the EmailNotification class.

        Args:
            conf_name (str): The name of the configuration. Defaults to "email".

        Returns:
            None
        """
        self._conf = get_ext_conf(name=conf_name)
        self._sender = self._conf.get("sender")
        self._password = self._conf.get("password")
        self._server = self._conf.get("server")
        self._recipients = self._conf.get("recipients")

    @staticmethod
    def _zip_file(target_dir: str, zip_path: str) -> None:
        """
        Compresses a directory into a zip file.

        Args:
            target_dir (str): The directory to be zipped.
            zip_path (str): Path to the output zip file.

        Returns:
            None
        """
        zip_instance = zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED)

        for path, _, filenames in os.walk(target_dir):
            relevant_path = path.replace(target_dir, "")
            for filename in filenames:
                if ".gitkeep" in filename or ".zip" in filename:
                    continue
                zip_instance.write(
                    os.path.abspath(os.path.join(path, filename)),
                    os.path.abspath(os.path.join(relevant_path, filename))
                )

        zip_instance.close()

    @staticmethod
    def _add_attachment(msg: MIMEMultipart, target_dir: str) -> MIMEMultipart:
        """
        Add attachments from a directory to an email message.

        Args:
            msg (MIMEMultipart): Email message to which attachments will be added.
            target_dir (str): The directory containing the attachments.

        Returns:
            MIMEMultipart: Updated email message with attachments added.
        """
        if not os.path.exists(target_dir):
            return msg

        filename = os.path.basename(target_dir)
        f = MIMEApplication(open(target_dir, "rb").read())
        f.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(f)

        return msg

    def send_email(self) -> None:
        """
        Send an email with attachments to specified recipients.

        Returns:
            None
        """

        msg = MIMEMultipart()
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        subject = "Test finished at " + now
        msg["Subject"] = subject
        msg["from"] = self._sender
        msg["to"] = self._recipients
        
        report_zip_path = os.path.abspath(os.path.join(report_dir, "report.zip"))
        EmailNotification._zip_file(report_dir, report_zip_path)
        msg = EmailNotification._add_attachment(msg, report_zip_path)

        log_zip_path = os.path.abspath(os.path.join(log_dir, "log.zip"))
        EmailNotification._zip_file(log_dir, log_zip_path)
        msg = EmailNotification._add_attachment(msg, log_zip_path)

        for filename in os.listdir(log_summary_dir):
            if filename == "summary.log":
                log_summary_path = os.path.abspath(os.path.join(log_summary_dir, "summary.log"))
                with open(log_summary_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines:
                        msg.attach(MIMEText(line, "plain", _charset="utf-8"))

        smtp = smtplib.SMTP()
        try:
            smtp.connect(self._server)
            smtp.login(self._sender, self._password)
            smtp.sendmail(self._sender, self._recipients.split(","), msg.as_string())
        except Exception as e:
            logger.error(f"{e}\n{traceback.format_exc()}")
        finally:
            if smtp:
                smtp.quit()


def send_email():
    EmailNotification().send_email()
