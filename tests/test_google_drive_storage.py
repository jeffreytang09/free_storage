import os

import pytest

from ..free_storage._google_drive_storage import GoogleDriveStorage


@pytest.fixture(scope="module")
def google_drive() -> GoogleDriveStorage:
    secret_dir = "secrets"
    settings_path = os.path.join(secret_dir, "gdrive_settings.yaml")
    cred_path = os.path.join(secret_dir, "gdrive_credentials.json")
    return GoogleDriveStorage(
        setting_file_name=settings_path, credential_file_name=cred_path
    )


def test_data_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def test_create_dir(google_drive: GoogleDriveStorage) -> None:
    google_drive.create_file("test")
    google_drive.create_file("test/sub_dir_1")
    google_drive.create_file("test/sub_dir_2")
    assert google_drive.path_exists("test") is not None
    assert google_drive.path_exists("test/sub_dir_1") is not None
    assert google_drive.path_exists("test/sub_dir_2") is not None


def test_create_zip_file(google_drive: GoogleDriveStorage) -> None:
    google_drive.create_file(
        remote_path="test/sub_dir_1/test.zip",
        local_path=os.path.join(test_data_path(), "test.zip"),
    )
    assert google_drive.path_exists("test/sub_dir_1/test.zip") is not None


def test_create_json_file(google_drive: GoogleDriveStorage) -> None:
    google_drive.create_file(
        remote_path="test/sub_dir_2/test.json",
        local_path=os.path.join(test_data_path(), "test.json"),
    )
    assert google_drive.path_exists("test/sub_dir_2/test.json") is not None


def test_create_txt_file(google_drive: GoogleDriveStorage) -> None:
    google_drive.create_file(
        remote_path="test/sub_dir_1/test.txt",
        local_path=os.path.join(test_data_path(), "test.txt"),
    )
    assert google_drive.path_exists("test/sub_dir_1/test.txt") is not None


def test_list_dir(google_drive: GoogleDriveStorage) -> None:
    sub_dir_1_files = google_drive.list_files("test/sub_dir_1")
    sub_dir_2_files = google_drive.list_files("test/sub_dir_2")
    assert set(sub_dir_1_files) == {"test.zip", "test.txt"}
    assert set(sub_dir_2_files) == {"test.json"}


def test_download_files(google_drive: GoogleDriveStorage) -> None:
    local_write_path = os.path.join(test_data_path(), "test_download.txt")
    google_drive.download_file(
        remote_path="test/sub_dir_1/test.txt", local_path=local_write_path
    )
    with open(local_write_path) as f:
        assert f.read().strip() == "test"
    os.remove(local_write_path)


def test_delete_files(google_drive: GoogleDriveStorage) -> None:
    google_drive.delete_file("test/sub_dir_1/test.txt")
    assert google_drive.path_exists("test/sub_dir_1/test.txt") is None
    assert google_drive.path_exists("test/sub_dir_1/test.zip") is not None
    assert google_drive.path_exists("test/sub_dir_2/test.json") is not None

    google_drive.delete_file("test/sub_dir_1")
    assert google_drive.path_exists("test/sub_dir_1/test.txt") is None
    assert google_drive.path_exists("test/sub_dir_1/test.zip") is None
    assert google_drive.path_exists("test/sub_dir_2/test.json") is not None

    google_drive.delete_file("test")
    assert google_drive.path_exists("test") is None
    assert google_drive.path_exists("test/sub_dir_1/test.txt") is None
    assert google_drive.path_exists("test/sub_dir_1/test.zip") is None
    assert google_drive.path_exists("test/sub_dir_2/test.json") is None
