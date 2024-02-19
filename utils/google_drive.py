# -*- coding: utf-8 -*-
import os
import filelock
import traceback
from utils.logger import logger
from types import TracebackType
from utils.common import get_conf
from utils.dirs import tmp_dir, lock_dir
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


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

    def __init__(self, google_conf_name: str = "google_api") -> None:
        """
        Initialize an instance of the GoogleDrive class.

        Args:
            google_conf_name (str): The name of the GoogleDrive configuration. Defaults to "google_api".

        Returns:
            None
        """
        self._lock = filelock.FileLock(os.path.abspath(os.path.join(lock_dir, "google_drive.lock")))
        self._google_conf = get_conf(name=google_conf_name)
        self._credentials = None
        self._drive_service = None
        self._init()

    def __enter__(self) -> 'GoogleDrive':
        """
        Context manager method for entering the context.

        Returns:
            GoogleDrive: The current instance of the GoogleDrive class.
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
        Initialize the credentials and drive_service.

        Returns:
            None
        """
        os.makedirs(tmp_dir, exist_ok=True)
        google_token_path = os.path.abspath(os.path.join(tmp_dir, "google_drive_token.json"))
        if os.path.exists(google_token_path):
            self._credentials = Credentials.from_authorized_user_file(
                filename=google_token_path,
                scopes=["https://www.googleapis.com/auth/drive",
                        "https://www.googleapis.com/auth/drive.metadata"]
            )

        if not self._credentials or not self._credentials.valid:
            if self._credentials and self._credentials.expired and self._credentials.refresh_token:
                self._credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    client_config=self._google_conf.get("client_config"),
                    scopes=["https://www.googleapis.com/auth/drive",
                            "https://www.googleapis.com/auth/drive.metadata"]
                )
                self._credentials = flow.run_local_server(port=0)
            with open(google_token_path, "w") as f:
                f.write(self._credentials.to_json())

        self._drive_service = build("drive", "v3", credentials=self._credentials)

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
            "parents": [parent_folder_id]
        }

        response = self._drive_service.files().create(body=file_metadata, fields="id").execute()
        folder_id = response.get("id")
        if folder_id is not None:
            logger.info(f"created folder {folder_name}")
        else:
            logger.error(f"failed to create folder, file will be uploaded to root, response: {response}")
        return folder_id
    
    def _get_folder_id(self, folder_name: str) -> str:
        """
            Get the ID of a folder by its name.

            Args:
                folder_name (str): The name of the folder to search for.

            Returns:
                str: The ID of the folder if found, otherwise None.
            """
        response = self._drive_service.files().list(
            q=f"""name="{folder_name}" and mimeType="application/vnd.google-apps.folder" """).execute()

        folders = response.get("files", [])
        if folders:
            folder_id = folders[0].get("id")
        else:
            logger.error(f"folder {folder_name} not found")
            folder_id = self._create_folder(folder_name=folder_name)

        return folder_id

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

        folder_name = self._google_conf.get("google_drive").get("folder_name")
        if not folder_name:
            folder_name = "test"

        folder_id = self._get_folder_id(folder_name=folder_name)
        file_metadata.update({"parents": [folder_id]})

        media = MediaFileUpload(file_path)
        with self._lock:
            response = self._drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()

        if response.get("id") is not None:
            logger.info(f"""uploaded {file_path} to folder {folder_name}, id: {response.get("id")}""")
            return True
        else:
            logger.error(f"failed to upload, response: {response}")
            return False


if __name__ == "__main__":
    GoogleDrive().upload_file(file_path="")
