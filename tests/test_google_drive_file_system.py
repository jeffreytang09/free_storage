import pytest

from ..free_storage._google_drive_file import (
    GOOGLE_FOLDER_TYPE,
    GOOGLE_TEXT_FILE_TYPE,
    FileId,
    FileName,
    RootNotDefinedException,
)
from ..free_storage._google_drive_file_system import (
    FileNotExistException,
    GoogleDriveFileSystem,
    GoogleDriveObjectList,
    NotAFolderException,
)


def get_file_object_list() -> GoogleDriveObjectList:
    return [
        {
            "id": "1dxJ_wfwpyopaxsOQZizCUK4s1JgKwRAN",
            "title": "test.txt",
            "mimeType": "text/plain",
            "parents": [
                {
                    "kind": "drive#parentReference",
                    "id": "14t8PlmxEalPgG_-TB1ed8MaqhPSOKWow",
                    "isRoot": False,
                }
            ],
        },
        {
            "id": "14t8PlmxEalPgG_-TB1ed8MaqhPSOKWow",
            "title": "indeed",
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [
                {
                    "kind": "drive#parentReference",
                    "id": "1JbGTXzAviTjbgp2IQEPpkUbrDBuNHN-J",
                    "isRoot": False,
                }
            ],
        },
        {
            "id": "1321343nkdsfnc22r4kjrknj3k",
            "title": "linkedin_test.txt",
            "mimeType": "text/plain",
            "parents": [
                {
                    "kind": "drive#parentReference",
                    "id": "14t8PlmxEalPgG_-dfdsferesrWEWEWW",
                    "isRoot": False,
                }
            ],
        },
        {
            "id": "14t8PlmxEalPgG_-dfdsferesrWEWEWW",
            "title": "linkedin",
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [
                {
                    "kind": "drive#parentReference",
                    "id": "1JbGTXzAviTjbgp2IQEPpkUbrDBuNHN-J",
                    "isRoot": False,
                }
            ],
        },
        {
            "id": "1JbGTXzAviTjbgp2IQEPpkUbrDBuNHN-J",
            "title": "data",
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [
                {
                    "kind": "drive#parentReference",
                    "id": "0APyTMT4xIggTUk9PVA",
                    "isRoot": True,
                }
            ],
        },
        {
            "id": "1JbGTXzAviTjbdcdsdffsfdsdfdsHN-J",
            "title": "data_2",
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [
                {
                    "kind": "drive#parentReference",
                    "id": "0APyTMT4xIggTUk9PVA",
                    "isRoot": True,
                }
            ],
        },
    ]


@pytest.fixture(scope="module")
def google_file_system() -> GoogleDriveFileSystem:
    gfs = GoogleDriveFileSystem()
    gfs.build(get_file_object_list())
    return gfs


def test_root_defined() -> None:
    with pytest.raises(RootNotDefinedException):
        gfs = GoogleDriveFileSystem()
        _ = gfs.root
    gfs.build(get_file_object_list())
    assert gfs._root is not None


def test_path_without_root_prefix(google_file_system: GoogleDriveFileSystem) -> None:
    test_file = google_file_system.file_exists("data")
    assert test_file is not None


def test_path_not_exist(google_file_system: GoogleDriveFileSystem) -> None:
    test_file = google_file_system.file_exists("not_existent")
    assert test_file is None


def test_listing_path_not_exist(google_file_system: GoogleDriveFileSystem) -> None:
    with pytest.raises(FileNotExistException):
        google_file_system.list_file("not_existent")


def test_listing_non_folder(google_file_system: GoogleDriveFileSystem) -> None:
    with pytest.raises(NotAFolderException):
        google_file_system.list_file("root/data/indeed/test.txt")


def test_listing_first_level(google_file_system: GoogleDriveFileSystem) -> None:
    root_level_file_names = google_file_system.list_file("root")
    expected_values = {FileName("data"), FileName("data_2")}
    assert set(root_level_file_names) == expected_values


def test_listing_second_level(google_file_system: GoogleDriveFileSystem) -> None:
    file_names_data = google_file_system.list_file("root/data")
    file_names_data_2 = google_file_system.list_file("root/data_2")
    expected_values_data = {FileName("linkedin"), FileName("indeed")}
    assert set(file_names_data) == expected_values_data
    assert len(set(file_names_data_2)) == 0


def test_listing_thrid_level(google_file_system: GoogleDriveFileSystem) -> None:
    file_names_indeed = google_file_system.list_file("root/data/indeed")
    expected_values_indeed = {FileName("test.txt")}
    assert set(file_names_indeed) == expected_values_indeed


def test_file_details(google_file_system: GoogleDriveFileSystem) -> None:
    indeed_file = google_file_system.file_exists("root/data/indeed")
    assert indeed_file is not None
    assert indeed_file.file_name == FileName("indeed")
    assert indeed_file.file_id == FileId("14t8PlmxEalPgG_-TB1ed8MaqhPSOKWow")
    assert indeed_file.file_type == GOOGLE_FOLDER_TYPE

    test_file = google_file_system.file_exists("root/data/indeed/test.txt")
    assert test_file is not None
    assert test_file.file_name == FileName("test.txt")
    assert test_file.file_id == FileId("1dxJ_wfwpyopaxsOQZizCUK4s1JgKwRAN")
    assert test_file.file_type == GOOGLE_TEXT_FILE_TYPE


def test_normalized_path(google_file_system: GoogleDriveFileSystem) -> None:
    file_names_data = google_file_system.list_file("data")
    file_names_data_2 = google_file_system.list_file("root/data_2")
    expected_values_data = {FileName("linkedin"), FileName("indeed")}
    assert set(file_names_data) == expected_values_data
    assert len(set(file_names_data_2)) == 0
