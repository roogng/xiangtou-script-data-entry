# db.py
import pymysql
from config_loader import Config
from pymysql.cursors import DictCursor


class MySQL:
    def __init__(self, conn):
        self._conn = conn

    @classmethod
    def from_config(cls, cfg: Config):
        m = cfg["mysql"]
        conn = pymysql.connect(
            host=m["host"], port=int(m["port"]), user=m["user"],
            password=m["password"], database=m["database"],
            charset="utf8mb4", autocommit=False, cursorclass=DictCursor,
        )
        return cls(conn)

    def execute(self, sql, args=None):
        with self._conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.lastrowid

    def query(self, sql, args=None):
        with self._conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()

    def query_one(self, sql, args=None):
        with self._conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()
