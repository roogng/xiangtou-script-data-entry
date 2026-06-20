# village_repo.py

_FETCH_SQL = """SELECT id, village_name, province_id, province_name, city_id, city_name,
  area_id, area_name, street_id, street_name, address, lng, lat
FROM vill_village WHERE id = %s"""


class VillageRepo:
    def __init__(self, db):
        self._db = db

    def fetch(self, village_id):
        return self._db.query_one(_FETCH_SQL, (village_id,))
