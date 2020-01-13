import os
from typing import List, Optional, TextIO, cast

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import ApiRequestError

from ._cloud_storage import CloudStorage
from ._google_drive_file import (
    GOOGLE_FOLDER_TYPE,
    FileNotExistException,
    NotAFolderException,
)
from ._google_drive_file_system import GoogleDriveFileSystem, GoogleDriveObjectList


class GoogleCredentialsNotFoundException(Exception):
    pass


class DriverNotDefined(Exception):
    pass


class GoogleDriveStorage(CloudStorage):
    def __init__(
        self, setting_file_name: str, credential_file_name: str, retry_limit: int = 5,
    ) -> None:
        super().__init__(retry_limit=retry_limit, api_error=ApiRequestError)
        self._setting_file_name = os.path.expanduser(setting_file_name)
        self._credential_file_name = os.path.expanduser(credential_file_name)
        self.connect()
        self.fs = GoogleDriveFileSystem()
        self._build_local_file_system()

    @property
    def drive(self) -> GoogleDrive:
        if self._drive is None:
            raise DriverNotDefined
        return self._drive

    def _build_local_file_system(self) -> None:
        """
        Pull list of file objects from Google Drive and build a local copy of the file system
        """
        response = self._run_command(
            command=self.drive.ListFile, params={"param": {"q": "trashed=false"}}
        )
        self.fs.build(cast(GoogleDriveObjectList, response.GetList()))

    def connect(self) -> None:
        def _connect() -> GoogleDrive:
            gauth = GoogleAuth(settings_file=self._setting_file_name)
            # Try to load saved client credentials
            gauth.LoadCredentialsFile(self._credential_file_name)
            if gauth.credentials is None:
                raise GoogleCredentialsNotFoundException(
                    f"{self._credential_file_name} not found"
                )
            elif gauth.access_token_expired:
                # Refresh them if expired
                gauth.Refresh()
            else:
                # Initialize the saved creds
                gauth.Authorize()
            # Save the current credentials to a file
            gauth.SaveCredentialsFile(self._credential_file_name)
            drive = GoogleDrive(gauth)
            # Actually try to connect to the drive
            drive.GetAbout()
            return drive

        self._drive = cast(GoogleDrive, self._run_command(command=_connect))
        assert self.is_connected()

    def is_connected(self) -> bool:
        # when the connection is not yet initiated
        if self._drive is None:
            return False
        # test the initiated connection and see if it fails
        http_conn = list(self._drive.http.connections.values())[0]
        return http_conn.sock is not None

    def reconnect(self) -> None:
        if self.is_connected():
            return
        self.connect()
        self.fs = GoogleDriveFileSystem()
        self._build_local_file_system()

    def close(self) -> None:
        gauth: GoogleAuth = self.drive.auth
        for conn in gauth.Get_Http_Object().connections.values():
            conn.close()

    def list_files(self, remote_path: str) -> List[str]:
        self.reconnect()
        file_to_list = self.fs.file_exists(remote_path)
        if file_to_list is None:
            raise FileNotExistException("Can't list path that doesn't exist")
        if file_to_list.file_type != GOOGLE_FOLDER_TYPE:
            raise NotAFolderException("Can't list non-folder")
        if file_to_list.children is None:
            raise NotAFolderException("Can't list non-folder")
        return [str(f) for f in file_to_list.children.keys()]

    def path_exists(self, remote_path: str) -> Optional[str]:
        self.reconnect()
        current_file = self.fs.file_exists(remote_path)
        return None if current_file is None else current_file.file_id

    def download_file(self, remote_path: str, local_path: Optional[str] = None) -> None:
        self.reconnect()
        file_id = self.path_exists(remote_path)
        if file_id is None:
            raise FileNotExistException("File doesn't exist. Cannot download")
        else:
            file_to_download = self.drive.CreateFile({"id": file_id})
            if local_path is None:
                _, local_path = os.path.split(remote_path)
            self._run_command(
                command=file_to_download.GetContentFile, params={"filename": local_path}
            )

    def read_file(self, remote_path: str) -> TextIO:
        tmp_dir = ".tmp"
        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)
        _, file_name = os.path.split(remote_path)
        tmp_file_path = str(os.path.join(tmp_dir, file_name))
        self.download_file(remote_path, tmp_file_path)
        tmp_file_obj = open(tmp_file_path)
        os.remove(tmp_file_path)
        return tmp_file_obj

    def create_file(
        self,
        remote_path: str,
        content: Optional[str] = None,
        local_path: Optional[str] = None,
    ) -> None:
        """
        Function for transferring files or making folders.
        If content and local_path are None then folder will be created
        """
        self.reconnect()
        existing_path, file_name = os.path.split(remote_path)
        parent_file = self.fs.file_exists(existing_path)
        if parent_file is None:
            raise FileNotExistException(
                "Parent file doesn't exists. Can't write to a non-existent folder"
            )
        if parent_file.file_type != GOOGLE_FOLDER_TYPE:
            raise NotAFolderException(
                "Parent file is not a directory. Can't write to a non dir"
            )
        # Setup the metadata for remote file to upload
        if local_path:
            gdrive_file_to_upload = self.drive.CreateFile(
                {"title": file_name, "parents": [{"id": parent_file.file_id}]}
            )
            gdrive_file_to_upload.SetContentFile(local_path)
        elif content:
            gdrive_file_to_upload = self.drive.CreateFile(
                {"title": file_name, "parents": [{"id": parent_file.file_id}]}
            )
            gdrive_file_to_upload.SetContentString(content)
        else:
            # if no content / local file is provided, create a folder
            gdrive_file_to_upload = self.drive.CreateFile(
                {
                    "title": file_name,
                    "parents": [{"id": parent_file.file_id}],
                    "mimeType": "application/vnd.google-apps.folder",
                }
            )
        self._run_command(command=gdrive_file_to_upload.Upload)
        # After upload, rebuild file system and confirm path exists
        self._build_local_file_system()
        assert self.fs.file_exists(remote_path)

    def delete_file(self, remote_path: str) -> None:
        self.reconnect()
        file_to_delete = self.fs.file_exists(remote_path)
        if file_to_delete is None:
            raise FileNotExistException("File doesn't exist. Can't delete")
        gdrive_file_to_delete = self.drive.CreateFile({"id": file_to_delete.file_id})
        self._run_command(command=gdrive_file_to_delete.Delete)
        # After delete, rebuild file system and confirm path doesn't exists
        self._build_local_file_system()
        assert self.fs.file_exists(remote_path) is None
