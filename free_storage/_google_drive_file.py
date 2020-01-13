from typing import Dict, List, NewType, Optional

GOOGLE_FOLDER_TYPE = "application/vnd.google-apps.folder"
GOOGLE_TEXT_FILE_TYPE = "text/plain"
GOOGLE_JSON_FILE_TYPE = "application/json"
GOOGLE_ZIP_FILE_TYPE = "application/zip"

FileId = NewType("FileId", str)
FileName = NewType("FileName", str)
FileType = NewType("FileType", str)
ChildrenType = Dict[FileName, "GoogleDriveFile"]


class NotAFolderException(Exception):
    pass


class RootNotDefinedException(Exception):
    pass


class FileNotExistException(Exception):
    pass


class FileAlreadyExistException(Exception):
    pass


class CannotAssignSubDirectoryToFileException(Exception):
    pass


class GoogleDriveFile:
    def __init__(
        self,
        file_name: FileName,
        file_id: FileId,
        file_type: FileType,
        children: Optional[ChildrenType] = None,
    ) -> None:
        self._file_name = file_name
        self._file_id = file_id
        self._file_type = file_type
        self._children = self.initiate_children(children, file_type)

    @staticmethod
    def initiate_children(
        children: Optional[ChildrenType], file_type: str
    ) -> Optional[ChildrenType]:
        if children is not None:
            return children
        return {} if file_type == GOOGLE_FOLDER_TYPE else None

    def update_children(self, children_files: List["GoogleDriveFile"]) -> None:
        if self.children is None or self.file_type != GOOGLE_FOLDER_TYPE:
            raise CannotAssignSubDirectoryToFileException
        for child_file in children_files:
            self.children.update({FileName(child_file.file_name): child_file})

    @property
    def file_name(self) -> FileName:
        return self._file_name

    @property
    def file_id(self) -> FileId:
        return self._file_id

    @property
    def file_type(self) -> FileType:
        return self._file_type

    @property
    def children(self) -> Optional[ChildrenType]:
        return self._children

    def get_child(self, file_name: FileName) -> Optional["GoogleDriveFile"]:
        if self.children is None:
            return None
        return self.children.get(file_name)

    def remove_child(self, file_name: FileName) -> None:
        assert self.children is not None
        if file_name not in self.children:
            raise FileNotExistException(
                "File not in specified directory. Cannot remove non-existent file"
            )
        del self.children[file_name]
