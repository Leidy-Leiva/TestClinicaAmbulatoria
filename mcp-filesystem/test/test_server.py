"""
Tests unitarios para el servidor MCP Filesystem.
Ejecutar con: pytest tests/test_server.py -v
"""

import os
import sys
import tempfile
import shutil
import pytest

# Directorio temporal como sandbox para tests
_tmp_root = tempfile.mkdtemp()
os.environ["FS_ROOT"] = _tmp_root
os.environ["MAX_FILE_SIZE_MB"] = "1"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import importlib
import server as srv
importlib.reload(srv)

from server import (
    read_file,
    write_file,
    append_file,
    list_directory,
    create_directory,
    delete_file,
    delete_directory,
    copy_file,
    move_file,
    get_file_info,
    search_files,
    get_disk_usage,
    safe_path,
    FS_ROOT,
)


@pytest.fixture(autouse=True)
def clean_workspace():
    """Limpia el workspace antes de cada test."""
    for item in FS_ROOT.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
    yield


# ── SEGURIDAD ──────────────────────────────────────────────────────────────────

def test_path_traversal_blocked():
    with pytest.raises(PermissionError):
        safe_path("../../etc/passwd")


def test_path_traversal_double_dot_blocked():
    with pytest.raises(PermissionError):
        safe_path("../outside")


def test_valid_nested_path():
    p = safe_path("folder/subfolder/file.txt")
    assert str(p).startswith(str(FS_ROOT))


# ── WRITE ─────────────────────────────────────────────────────────────────────

def test_write_file_basic():
    result = write_file("hello.txt", "Hello, World!")
    assert result["size_bytes"] > 0
    assert result["lines"] == 1


def test_write_file_creates_dirs():
    write_file("a/b/c/deep.txt", "nested content", create_dirs=True)
    assert (FS_ROOT / "a/b/c/deep.txt").exists()


def test_write_file_no_overwrite():
    write_file("exist.txt", "original")
    with pytest.raises(FileExistsError):
        write_file("exist.txt", "new content", overwrite=False)


def test_write_file_overwrite():
    write_file("file.txt", "v1")
    write_file("file.txt", "v2", overwrite=True)
    assert read_file("file.txt")["content"] == "v2"


# ── READ ──────────────────────────────────────────────────────────────────────

def test_read_file_basic():
    write_file("readme.txt", "line1\nline2\nline3")
    result = read_file("readme.txt")
    assert result["content"] == "line1\nline2\nline3"
    assert result["lines"] == 3


def test_read_file_not_found():
    with pytest.raises(FileNotFoundError):
        read_file("ghost.txt")


def test_read_file_is_directory():
    create_directory("mydir")
    with pytest.raises(IsADirectoryError):
        read_file("mydir")


# ── APPEND ────────────────────────────────────────────────────────────────────

def test_append_file_existing():
    write_file("log.txt", "line1\n")
    append_file("log.txt", "line2\n")
    content = read_file("log.txt")["content"]
    assert "line1" in content and "line2" in content


def test_append_file_creates_new():
    append_file("new_log.txt", "first entry\n")
    assert (FS_ROOT / "new_log.txt").exists()


# ── LIST ──────────────────────────────────────────────────────────────────────

def test_list_directory_empty():
    result = list_directory(".")
    assert result["total_items"] == 0


def test_list_directory_with_files():
    write_file("a.txt", "a")
    write_file("b.txt", "b")
    create_directory("subdir")
    result = list_directory(".")
    assert result["total_items"] == 3
    assert result["files"] == 2
    assert result["directories"] == 1


def test_list_directory_pattern():
    write_file("script.py", "# python")
    write_file("notes.txt", "notes")
    write_file("main.py", "# main")
    result = list_directory(".", pattern="*.py")
    assert result["files"] == 2


def test_list_directory_recursive():
    write_file("root.txt", "root")
    write_file("sub/deep.txt", "deep")
    result = list_directory(".", recursive=True)
    names = [i["name"] for i in result["items"]]
    assert "deep.txt" in names


def test_list_directory_hidden_excluded():
    write_file(".hidden", "secret")
    write_file("visible.txt", "public")
    result = list_directory(".", show_hidden=False)
    names = [i["name"] for i in result["items"]]
    assert ".hidden" not in names
    assert "visible.txt" in names


# ── CREATE DIRECTORY ──────────────────────────────────────────────────────────

def test_create_directory_basic():
    result = create_directory("newfolder")
    assert (FS_ROOT / "newfolder").is_dir()
    assert result["created"] is True


def test_create_directory_nested():
    create_directory("a/b/c")
    assert (FS_ROOT / "a/b/c").is_dir()


def test_create_directory_exist_ok_false():
    create_directory("exists")
    with pytest.raises(FileExistsError):
        create_directory("exists", exist_ok=False)


# ── DELETE ────────────────────────────────────────────────────────────────────

def test_delete_file_basic():
    write_file("temp.txt", "bye")
    result = delete_file("temp.txt")
    assert result["deleted"] is True
    assert not (FS_ROOT / "temp.txt").exists()


def test_delete_file_not_found():
    with pytest.raises(FileNotFoundError):
        delete_file("ghost.txt")


def test_delete_directory_empty():
    create_directory("emptydir")
    result = delete_directory("emptydir")
    assert result["deleted"] is True


def test_delete_directory_recursive():
    write_file("fulldir/file.txt", "content")
    result = delete_directory("fulldir", recursive=True)
    assert result["deleted"] is True
    assert not (FS_ROOT / "fulldir").exists()


def test_delete_directory_not_empty_fails():
    write_file("fulldir/file.txt", "content")
    with pytest.raises(OSError):
        delete_directory("fulldir", recursive=False)


# ── COPY & MOVE ───────────────────────────────────────────────────────────────

def test_copy_file_basic():
    write_file("original.txt", "data")
    copy_file("original.txt", "copy.txt")
    assert (FS_ROOT / "copy.txt").exists()
    assert (FS_ROOT / "original.txt").exists()


def test_copy_no_overwrite():
    write_file("src.txt", "src")
    write_file("dst.txt", "dst")
    with pytest.raises(FileExistsError):
        copy_file("src.txt", "dst.txt", overwrite=False)


def test_move_file_basic():
    write_file("source.txt", "move me")
    move_file("source.txt", "destination.txt")
    assert (FS_ROOT / "destination.txt").exists()
    assert not (FS_ROOT / "source.txt").exists()


def test_move_file_rename():
    write_file("old_name.txt", "content")
    move_file("old_name.txt", "new_name.txt")
    assert read_file("new_name.txt")["content"] == "content"


# ── GET FILE INFO ─────────────────────────────────────────────────────────────

def test_get_file_info_file():
    write_file("info_test.txt", "hello")
    info = get_file_info("info_test.txt")
    assert info["type"] == "file"
    assert info["size_bytes"] > 0
    assert "md5" in info
    assert "sha256" in info


def test_get_file_info_directory():
    create_directory("mydir")
    info = get_file_info("mydir")
    assert info["type"] == "directory"


def test_get_file_info_not_found():
    with pytest.raises(FileNotFoundError):
        get_file_info("nowhere.txt")


# ── SEARCH ────────────────────────────────────────────────────────────────────

def test_search_files_by_name():
    write_file("report_2024.txt", "annual report")
    write_file("summary.txt", "brief")
    write_file("report_2023.txt", "old report")
    result = search_files("report")
    assert result["total_matches"] == 2


def test_search_files_case_insensitive():
    write_file("README.md", "documentation")
    result = search_files("readme", case_sensitive=False)
    assert result["total_matches"] == 1


def test_search_files_in_content():
    write_file("notes.txt", "This file contains the keyword SECRET inside")
    write_file("other.txt", "Nothing relevant here")
    result = search_files("secret", search_content=True, case_sensitive=False)
    content_matches = [m for m in result["matches"] if m.get("matched_content")]
    assert len(content_matches) >= 1


# ── DISK USAGE ────────────────────────────────────────────────────────────────

def test_get_disk_usage_empty():
    result = get_disk_usage(".")
    assert result["file_count"] == 0
    assert result["total_size_bytes"] == 0


def test_get_disk_usage_with_files():
    write_file("a.txt", "hello")
    write_file("b.txt", "world")
    create_directory("subdir")
    write_file("subdir/c.txt", "nested")
    result = get_disk_usage(".")
    assert result["file_count"] == 3
    assert result["directory_count"] == 1
    assert result["total_size_bytes"] > 0


# ── ERRORES Y CASOS EXTREMOS ───────────────────────────────────────────────────

def test_read_file_too_large():
    os.environ["MAX_FILE_SIZE_MB"] = "0"
    import importlib
    import server as srv
    importlib.reload(srv)
    from server import write_file, read_file, MAX_FILE_BYTES
    
    os.environ["MAX_FILE_SIZE_MB"] = "1"
    importlib.reload(srv)
    from server import write_file, read_file
    
    write_file("small.txt", "x")
    with pytest.raises(ValueError, match="demasiado grande"):
        read_file("small.txt")


def test_write_file_content_too_large():
    os.environ["MAX_FILE_SIZE_MB"] = "1"
    import importlib
    import server as srv
    importlib.reload(srv)
    from server import write_file
    
    large_content = "x" * (11 * 1024 * 1024)
    with pytest.raises(ValueError, match="demasiado grande"):
        write_file("large.txt", large_content)


def test_delete_root_forbidden():
    with pytest.raises(PermissionError, match="raíz"):
        delete_file("/")


def test_delete_directory_root_forbidden():
    with pytest.raises(PermissionError, match="raíz"):
        delete_directory(".")


def test_copy_nonexistent_source():
    with pytest.raises(FileNotFoundError):
        copy_file("no_existe.txt", "destino.txt")


def test_move_nonexistent_source():
    with pytest.raises(FileNotFoundError):
        move_file("no_existe.txt", "destino.txt")


def test_list_directory_nonexistent():
    with pytest.raises(FileNotFoundError):
        list_directory("directorio_inexistente")


def test_create_directory_recursive():
    create_directory("a/b/c/d", exist_ok=True)
    assert (FS_ROOT / "a/b/c/d").is_dir()


def test_search_files_empty_query():
    result = search_files("")
    assert result["total_matches"] == 0


def test_search_files_with_results():
    write_file("match1.txt", "hello world")
    write_file("match2.txt", "hello python")
    write_file("no_match.txt", "foo bar")
    result = search_files("hello")
    assert result["total_matches"] >= 2


def test_file_info_hidden_file():
    write_file(".secret", "hidden content")
    info = get_file_info(".secret")
    assert info["type"] == "file"


def test_disk_usage_on_file_error():
    with pytest.raises(NotADirectoryError):
        get_disk_usage("a.txt")


# ── SEGURIDAD ADICIONAL ──────────────────────────────��─────────────────────

def test_path_traversal_absolute_windows():
    with pytest.raises(PermissionError):
        safe_path("C:\\windows\\system32\\config")


def test_path_traversal_with_null_byte():
    with pytest.raises(PermissionError):
        safe_path("..\\..\\etc/passwd\x00.txt")


def test_write_file_with_special_chars():
    special_name = "file with spaces and #tags.txt"
    write_file(special_name, "content", overwrite=True)
    assert (FS_ROOT / special_name).exists()


def test_read_file_encoding_invalid():
    write_file("binary.dat", "\x00\x01\x02")
    with pytest.raises(UnicodeDecodeError):
        read_file("binary.dat", encoding="utf-8")


def test_safe_path_edge_cases():
    assert safe_path("./././file.txt")
    assert safe_path("folder/../other/file.txt")
    with pytest.raises(PermissionError):
        safe_path("folder/../../outside")
