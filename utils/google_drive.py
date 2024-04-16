# -*- coding: utf-8 -*-
import os
import sys
import traceback
from types import TracebackType

import filelock
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from utils.common import get_ext_conf
from utils.dirs import lock_dir, tmp_dir
from utils.logger import logger


class GoogleDrive:
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
        Initialize an instance of the GoogleDrive class.

        Args:
            conf_name (str): The name of the configuration. Defaults to "google_api".

        Returns:
            None
        """
        self._lock = filelock.FileLock(
            os.path.abspath(os.path.join(lock_dir, "google_drive.lock"))
        )
        self._conf = get_ext_conf(name=conf_name)
        self._drive_service = None
        self._init()

    def __enter__(self) -> "GoogleDrive":
        """
        Context manager method for entering the context.

        Returns:
            GoogleDrive: The current instance of the GoogleDrive class.
        """
        return self

    def __exit__(
        self, exc_type: type, exc_val: BaseException, exc_tb: TracebackType
    ) -> None:
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
            logger.error(f"""{exc_val}\n{"".join(traceback.format_tb(exc_tb))}""")

    def _init(self) -> None:
        """
        Initialize the drive_service.

        Returns:
            None
        """
        credentials = service_account.Credentials.from_service_account_info(
            info=self._conf.get("service_info"),
            scopes=[
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/drive.metadata",
            ],
        )
        self._drive_service = build(
            serviceName="drive", version="v3", credentials=credentials
        )

    def _create_folder(self, folder_name: str, parent_folder_id: str = None) -> str:
        """
        Create a new folder in Google Drive.

        Args:
            folder_name (str): The name of the folder to create.
            parent_folder_id (str): The ID of the parent folder. Default is None (create in root).

        Returns:
            str: The ID of the newly created folder, or None if creation failed.
        """
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_folder_id],
        }

        response = (
            self._drive_service.files()
            .create(body=file_metadata, fields="id")
            .execute()
        )
        folder_id = response.get("id")
        if folder_id is not None:
            logger.info(f"created folder {folder_name}")
        else:
            logger.warning(
                f"create folder ({folder_name}) failed, file will be uploaded to root, response: {response}"
            )
        return folder_id

    def _get_id(self, name: str) -> str:
        """
        Get the ID of a folder/file by its name.

        Args:
            name (str): The name of the folder/file to search for.

        Returns:
            str: The ID of the folder/file if found, otherwise empty string.
        """
        response = self._drive_service.files().list(q=f""" name="{name}" """).execute()

        files = response.get("files", [])
        if files:
            if len(files) > 1:
                logger.error(f"too many results for name: {name}")
                sys.exit(1)
            result_id = files[0].get("id")
        else:
            logger.warning(f"no search result for name {name}")
            result_id = ""

        return result_id

    def upload_file(self, file_path: str, file_name: str = None) -> bool:
        """
        Upload a file to Google Drive.

        Args:
            file_path (str): Path to the file to upload.
            file_name (str): Name of the file on Google Drive. Default is None (use raw filename).

        Returns:
            bool: True if the file was uploaded successfully, False otherwise.
        """
        file_metadata = {}
        if file_name is None:
            file_name = os.path.basename(file_path)
        file_metadata.update({"name": file_name})

        folder_name = self._conf.get("google_drive").get("folder_name")
        if not folder_name:
            folder_name = "tmp"

        folder_id = self._get_id(name=folder_name)
        if not folder_id:
            folder_id = self._create_folder(folder_name=folder_name)

        file_metadata.update({"parents": [folder_id]})

        media = MediaFileUpload(file_path)
        with self._lock:
            response = (
                self._drive_service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )

        if response.get("id") is not None:
            logger.info(
                f"""uploaded {file_path} to folder {folder_name}, id: {response.get("id")}"""
            )
            return True
        else:
            logger.error(f"failed to upload, response: {response}")
            return False

    def download_file(self, file_name: str, destination_path: str = None) -> bool:
        """
        Download a file from Google Drive.

        Args:
            file_name (str): The name of the file to download.
            destination_path (str): The local path to save the downloaded file.

        Returns:
            bool: True if the file was downloaded successfully, False otherwise.
        """
        file_id = self._get_id(name=file_name)
        if not file_id:
            return False

        response = self._drive_service.files().get_media(fileId=file_id)

        if destination_path is None:
            destination_path = os.path.abspath(os.path.join(tmp_dir, file_name))

        with open(destination_path, "wb") as file:
            downloader = MediaIoBaseDownload(file, response)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                logger.info(f"progress: {int(status.progress() * 100)}%")

        logger.info(f"downloaded file {file_name} to {destination_path}")
        return True

    def delete_file(self, file_name: str) -> bool:
        """
        Delete a file from Google Drive.

        Args:
            file_name (str): The name of the file to delete.

        Returns:
            bool: True if the file was deleted successfully, False otherwise.
        """
        file_id = self._get_id(name=file_name)
        if not file_id:
            return False

        with self._lock:
            self._drive_service.files().delete(fileId=file_id).execute()

        logger.info(f"deleted file {file_name} from Google Drive")
        return True


if __name__ == "__main__":
    try:
        # files will be managed in Google Drive of the service account
        GoogleDrive().upload_file(file_path="")
    except Exception as e:
        logger.error(f"{e}\n{traceback.format_exc()}")
