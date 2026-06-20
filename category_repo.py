# category_repo.py

_LOAD_SQL = ("SELECT category_id, category_name FROM t_category "
             "WHERE parent_id > 0 AND deleted_flag = 0")


class CategoryRepo:
    """Loads goods sub-categories (parent_id > 0) once, maps name -> category_id."""

    def __init__(self, db):
        self._db = db
        self._map = None

    def _load(self):
        rows = self._db.query(_LOAD_SQL)
        self._map = {r["category_name"]: r["category_id"] for r in rows}

    def get(self, name):
        if self._map is None:
            self._load()
        return self._map.get((name or "").strip())
