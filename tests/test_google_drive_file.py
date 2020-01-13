import pytest

from ..free_storage._google_drive_file import (
    GOOGLE_FOLDER_TYPE,
    GOOGLE_TEXT_FILE_TYPE,
    CannotAssignSubDirectoryToFileException,
    FileId,
    FileName,
    FileType,
    GoogleDriveFile,
)


def gen_child(child_id: int) -> GoogleDriveFile:
    return GoogleDriveFile(
        file_name=FileName(f"child_{child_id}"),
        file_id=FileId(f"child_id_{child_id}"),
        file_type=FileType(GOOGLE_FOLDER_TYPE),
    )


def test_properties_dir() -> None:
    test_file = GoogleDriveFile(
        file_name=FileName("test"),
        file_id=FileId("test_id"),
        file_type=FileType(GOOGLE_FOLDER_TYPE),
    )
    assert test_file.file_name == FileName("test")
    assert test_file.file_id == FileId("test_id")
    assert test_file.file_type == FileType(GOOGLE_FOLDER_TYPE)


def test_properties_non_dir() -> None:
    test_file = GoogleDriveFile(
        file_name=FileName("test"),
        file_id=FileId("test_id"),
        file_type=FileType(GOOGLE_TEXT_FILE_TYPE),
    )
    assert test_file.file_name == FileName("test")
    assert test_file.file_id == FileId("test_id")
    assert test_file.file_type == FileType(GOOGLE_TEXT_FILE_TYPE)


def test_initiate_children_dir_no_initial_children():
    test_file = GoogleDriveFile(
        file_name=FileName("test"),
        file_id=FileId("test_id"),
        file_type=FileType(GOOGLE_FOLDER_TYPE),
    )
    assert test_file.children == {}


def test_initiate_children_non_dir_no_initial_children():
    test_file = GoogleDriveFile(
        file_name=FileName("test"),
        file_id=FileId("test_id"),
        file_type=FileType(GOOGLE_TEXT_FILE_TYPE),
    )
    assert test_file.children is None


def test_update_children_non_dir():
    child_1 = gen_child(1)
    test_file = GoogleDriveFile(
        file_name=FileName("test"),
        file_id=FileId("test_id"),
        file_type=FileType(GOOGLE_TEXT_FILE_TYPE),
    )
    with pytest.raises(CannotAssignSubDirectoryToFileException):
        test_file.update_children([child_1])


def test_update_children_dir_no_initial_children():
    child_1 = gen_child(1)
    children_dict = {child_1.file_name: child_1}
    test_file = GoogleDriveFile(
        file_name=FileName("test"),
        file_id=FileId("test_id"),
        file_type=FileType(GOOGLE_FOLDER_TYPE),
    )
    test_file.update_children([child_1])
    assert test_file.children == children_dict

    child_2 = gen_child(2)
    children_dict = {child_1.file_name: child_1, child_2.file_name: child_2}
    test_file.update_children([child_2])
    assert test_file.children == children_dict

    child_3 = gen_child(3)
    child_4 = gen_child(4)
    children_dict = {
        child_1.file_name: child_1,
        child_2.file_name: child_2,
        child_3.file_name: child_3,
        child_4.file_name: child_4,
    }
    test_file.update_children([child_3, child_4])
    assert test_file.children == children_dict


def test_update_children_dir_initial_children():
    child_1 = gen_child(1)
    children_dict = {child_1.file_name: child_1}
    test_file = GoogleDriveFile(
        file_name=FileName("test"),
        file_id=FileId("test_id"),
        file_type=FileType(GOOGLE_FOLDER_TYPE),
        children=children_dict,
    )
    assert test_file.children == children_dict

    child_2 = gen_child(2)
    child_3 = gen_child(3)
    children_dict = {
        child_1.file_name: child_1,
        child_2.file_name: child_2,
        child_3.file_name: child_3,
    }
    test_file.update_children([child_2, child_3])
    assert test_file.children == children_dict
