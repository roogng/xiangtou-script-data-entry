# tests/test_file_repo.py
from unittest.mock import MagicMock
from file_repo import FileRepo


def test_insert_returns_file_id_and_uses_defaults():
    db = MagicMock()
    db.execute.return_value = 99
    repo = FileRepo(db, creator_id=43, creator_user_type=1, creator_name="乡投会员5446")
    fid = repo.insert(file_key="public/common/abc.jpg", file_name="a.jpg",
                      file_size=1234, file_type="jpg")
    sql, args = db.execute.call_args.args
    assert "t_file" in sql
    assert args[0] == 1          # folder_type
    assert args[1] == "a.jpg"    # file_name
    assert args[2] == 1234       # file_size
    assert args[3] == "public/common/abc.jpg"
    assert args[4] == "jpg"
    assert args[5] == 43         # creator_id
    assert args[6] == 1          # creator_user_type
    assert args[7] == "乡投会员5446"
    assert fid == 99


def test_insert_truncates_long_file_name():
    # Pixabay hash filenames exceed t_file.file_name varchar(100); must truncate.
    db = MagicMock()
    repo = FileRepo(db, creator_id=43, creator_user_type=1, creator_name="x")
    long_name = "g" * 130 + ".jpg"
    repo.insert(file_key="public/common/k.jpg", file_name=long_name,
                file_size=123, file_type="jpg")
    args = db.execute.call_args.args[1]
    assert args[1] == ("g" * 100)   # file_name truncated to column max
