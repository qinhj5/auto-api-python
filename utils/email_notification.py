# -*- coding: utf-8 -*-
import os
import time
import zipfile
import smtplib
from utils.common import get_conf
from email.mime.text import MIMEText
from utils.dirs import report_dir, log_dir
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

EMAIL_CONF = get_conf(name="email")


class EmailNotification:
    def __init__(self, sender: str, password: str, server: str, recipients: str) -> None:
        """
        Initialize the class.

        Args:
            sender (str): The email address of the sender.
            password (str): The password of the sender's email account.
            server (str): The SMTP server address.
            recipients (str): Comma-separated list of email addresses of the recipients.

        Returns:
            None
        """
        self._sender = sender
        self._password = password
        self._server = server
        self._recipients = recipients

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
                zip_instance.write(os.path.join(path, filename), os.path.join(relevant_path, filename))

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
        for filename in os.listdir(target_dir):
            if ".zip" in filename:
                f = MIMEApplication(open(os.path.join(target_dir, filename), "rb").read())
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

        for filename in os.listdir(log_dir):
            if filename == "summary.log":
                with open(log_dir + "/" + filename, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines:
                        msg.attach(MIMEText(line, "plain", _charset="utf-8"))

        smtp = smtplib.SMTP()
        smtp.connect(self._server)
        smtp.login(self._sender, self._password)
        smtp.sendmail(self._sender, self._recipients.split(","), msg.as_string())
        smtp.quit()


def send_email():
    EmailNotification(**EMAIL_CONF).send_email()
