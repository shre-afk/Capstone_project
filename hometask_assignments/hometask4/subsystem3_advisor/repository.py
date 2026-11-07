"""Read energy summaries from MySQL; Flask routes contain no SQL."""

import pymysql

from .errors import AdvisorDatabaseError


class EnergyRepository:
    def __init__(self, settings):
        self._settings = dict(settings)

    def _query(self, sql, params=()):
        connection = None
        try:
            connection = pymysql.connect(**self._settings, cursorclass=pymysql.cursors.DictCursor)
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = list(cursor.fetchall())
                for row in rows:
                    row['report_date'] = row['report_date'].isoformat()
                return rows
        except pymysql.MySQLError as error:
            raise AdvisorDatabaseError('Unable to retrieve energy summaries.') from error
        finally:
            if connection is not None:
                connection.close()

    def list_summaries(self):
        return self._query('SELECT * FROM energy_summary ORDER BY building_id')

    def get_summary(self, building_id):
        rows = self._query('SELECT * FROM energy_summary WHERE building_id = %s', (building_id,))
        return rows[0] if rows else None
