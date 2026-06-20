# file_repo.py

_INSERT_SQL = """
INSERT INTO t_file
  (folder_type, file_name, file_size, file_key, file_type,
   creator_id, creator_user_type, creator_name)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
"""


class FileRepo:
    def __init__(self, db, creator_id, creator_user_type, creator_name):
        self._db = db
        self._creator_id = creator_id
        self._creator_user_type = creator_user_type
        self._creator_name = creator_name

    def insert(self, file_key, file_name, file_size, file_type):
        return self._db.execute(_INSERT_SQL, (
            1, file_name, file_size, file_key, file_type,
            self._creator_id, self._creator_user_type, self._creator_name,
        ))
