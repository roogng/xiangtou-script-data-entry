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
