# tests/test_category_repo.py
from unittest.mock import MagicMock
from category_repo import CategoryRepo


def test_get_returns_id_by_name():
    db = MagicMock()
    db.query.return_value = [{"category_id": 376, "category_name": "炒货"},
                             {"category_id": 381, "category_name": "茶叶"}]
    repo = CategoryRepo(db)
    assert repo.get("炒货") == 376
    assert repo.get("茶叶") == 381


def test_get_returns_none_for_unknown():
    db = MagicMock()
    db.query.return_value = [{"category_id": 376, "category_name": "炒货"}]
    repo = CategoryRepo(db)
    assert repo.get("不存在") is None


def test_get_strips_whitespace():
    db = MagicMock()
    db.query.return_value = [{"category_id": 376, "category_name": "炒货"}]
    repo = CategoryRepo(db)
    assert repo.get("  炒货  ") == 376


def test_loads_once_and_queries_parent_id_gt_zero():
    db = MagicMock()
    db.query.return_value = [{"category_id": 376, "category_name": "炒货"}]
    repo = CategoryRepo(db)
    repo.get("炒货")
    repo.get("炒货")
    assert db.query.call_count == 1
    sql = db.query.call_args.args[0]
    assert "parent_id > 0" in sql
    assert "deleted_flag = 0" in sql
