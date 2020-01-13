import logging
import os
from typing import Any, Dict, List, Optional

from ._google_drive_file import (
    GOOGLE_FOLDER_TYPE,
    FileId,
    FileName,
    FileNotExistException,
    FileType,
    GoogleDriveFile,
    NotAFolderException,
    RootNotDefinedException,
)

GoogleDriveObject = Dict[str, Any]
GoogleDriveObjectList = List[GoogleDriveObject]

ROOT_FILE_NAME = FileName("root")


# FileSystem assumes no 2 files will have same name but different types
# TODO: Add a function to check if there are dups in children (same name + type). Also no dup ids across files
class GoogleDriveFileSystem:
    """
    Building this to more easily navigate the file system on gdrive
    http://helpful-nerd.com/2018/01/30/folder-and-directory-management-for-google-drive-using-python/
    """

    def __init__(self,) -> None:
        self._root: Optional[GoogleDriveFile] = None

    @property
    def root(self) -> GoogleDriveFile:
        if self._root is None:
            raise RootNotDefinedException
        return self._root

    @staticmethod
    def _get_parent(file_object: GoogleDriveObject) -> GoogleDriveObject:
        # The parent field should only contain the immediate parent even tho it's a list
        parents = file_object["parents"]
        if len(parents) > 1:
            raise Exception("File has more than 1 parent")
        return parents[0]

    @staticmethod
    def _get_file_type(file_object: GoogleDriveObject) -> FileType:
        return file_object["mimeType"]

    @staticmethod
    def _get_file_name(file_object: GoogleDriveObject) -> FileName:
        return file_object["title"]

    @staticmethod
    def _get_id(file_object: GoogleDriveObject) -> FileId:
        return FileId(file_object["id"])

    def _get_parent_is_root(self, file_object: GoogleDriveObject) -> bool:
        return self._get_parent(file_object)["isRoot"]

    def _get_parent_id(self, file_object: GoogleDriveObject) -> FileId:
        return self._get_id(self._get_parent(file_object))

    def build(self, file_object_list: GoogleDriveObjectList) -> None:
        file_dict: Dict[FileId, GoogleDriveFile] = {}
        # First loop to make the files and store them in a dict
        for file_object in file_object_list:
            file_id = self._get_id(file_object)
            file_name = self._get_file_name(file_object)
            file_type = self._get_file_type(file_object)
            current_file = GoogleDriveFile(
                file_name=file_name, file_id=file_id, file_type=file_type
            )
            if self._get_parent_is_root(file_object):
                root_file_id = self._get_parent_id(file_object)
                if root_file_id not in file_dict:
                    file_dict[root_file_id] = GoogleDriveFile(
                        file_name=ROOT_FILE_NAME,
                        file_id=FileId(root_file_id),
                        file_type=FileType(GOOGLE_FOLDER_TYPE),
                    )
            file_dict[file_id] = current_file
        # Second loop to populate children field of the file
        for file_object in file_object_list:
            file_id = self._get_id(file_object)
            current_file = file_dict[file_id]
            # Get parent file and add current file to parent_file.children
            parent_file_id = self._get_parent_id(file_object)
            # Sometimes when we delete a folder remotely, the drive will still return
            # all their children file in the file_object_list even tho their parent is already deleted
            # So we can't find the parent in the file object list, we assume it's deleted and we move on
            try:
                parent_file = file_dict[parent_file_id]
                parent_file.update_children([current_file])
            except KeyError:
                continue
        root = [f for f in file_dict.values() if f.file_name == ROOT_FILE_NAME][0]
        self._root = root

    @staticmethod
    def _normalized_path_list(path: str) -> List[str]:
        if not path.startswith(ROOT_FILE_NAME):
            path = str(os.path.join(ROOT_FILE_NAME, path))
        # Filter out empty strings
        return [file_part for file_part in path.split("/") if file_part]

    def file_exists(self, path: str) -> Optional[GoogleDriveFile]:
        """
        If file exists, then return file node, else return None
        """
        current_file = self.root
        file_name_list = self._normalized_path_list(path)
        normalized_file_path = "/".join(file_name_list)
        logging.info(f"Checking if {normalized_file_path} exists...")
        last_index = len(file_name_list) - 1
        for index, file_name in enumerate(file_name_list):
            if current_file.file_name != FileName(file_name):
                return None
            # If not the last item in the path, then get the next file in the path and assign as root
            if index < last_index:
                next_file_name = FileName(file_name_list[index + 1])
                next_file = current_file.get_child(next_file_name)
                # If not last item in path and sub-files don't contain the next item, path doesn't exist
                if next_file is None:
                    return None
                current_file = next_file
            else:
                return current_file
        raise Exception("Not suppose to reach here. Check function file_exists")

    def list_file(self, path: str) -> List[FileName]:
        """
        Only will return list of files if the file is a directory
        """
        current_file = self.file_exists(path)
        if current_file is None:
            raise FileNotExistException(
                "Path doesn't exist. Can't list non-existent path"
            )
        if current_file.file_type != GOOGLE_FOLDER_TYPE:
            raise NotAFolderException("file_nod has to be a folder to list contents")
        if current_file.children is None:
            raise NotAFolderException("file_nod has to be a folder to list contents")
        if len(current_file.children) == 0:
            return []
        return [
            child_file.file_name for child_file in list(current_file.children.values())
        ]
