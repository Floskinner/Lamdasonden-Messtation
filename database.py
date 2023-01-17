import sqlite3
from datetime import datetime
from datetime import timedelta
from pathlib import Path


class Database:
    def __init__(self, db_file: Path):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cur = self.conn.cursor()
        self.__init_temp_values()
        self.__init_temp_sensor_tracking()
        self.__init_lambda_values()

        self.__clear_temp_values()
        self.__clear_lambda_values()

    def insert_temp_value(self, value: float):
        """Fügt einen Temperaturwert in die Datenbank mit dem Zeitstempel ein.

        :param value: Temperaturwert
        """
        timestamp_int = datetime.now()
        timestamp = timestamp_int.isoformat()
        self.execute("INSERT INTO temps VALUES (?, ?)", (timestamp, value))

    def insert_temp_sensor_tracking(self, sensor_id: int, time_run_in_sec: int):
        """Fügt einen neuen Sensor mit entsprechender Laufzeit in die Datenbank hinzu.

        :param sensor_id: Sensor ID
        :param time_run_in_sec: Laufzeit in Sekunden
        """
        self.execute("INSERT INTO temp_sensor_tracking VALUES (?, ?)", (sensor_id, time_run_in_sec))

    def insert_lambda_value(self, value: float):
        """Fügt einen Lambda-Wert in die Datenbank mit dem Zeitstempel ein.

        :param value: Lambda-Wert
        """
        timestamp_int = datetime.now()
        timestamp = timestamp_int.isoformat()
        self.execute("INSERT INTO lambda VALUES (?, ?)", (timestamp, value))

    def update_temp_sensor_tracking(self, time_run_in_sec: int):
        """Aktualisiert die Laufzeit des Sensors.

        :param time_run_in_sec: Laufzeit in Sekunden
        """
        self.execute("UPDATE temp_sensor_tracking SET time_run_in_sec = ?", (time_run_in_sec,))

    def get_temp_values(self) -> list:
        """Gibt alle Temperaturwerte aus der Datenbank zurück.

        :return: Temperaturwerte
        """
        self.cur.execute("SELECT * FROM temps")
        return self.cur.fetchall()

    def get_temp_values_between(self, start: str, end: str) -> list:
        """Gibt alle Temperaturwerte aus der Datenbank zwischen zwei Zeitpunkten zurück.

        :param start: Startzeitpunkt in ISO-Format
        :param end: Endzeit in ISO-Format
        :return: Temperaturwerte
        """
        start_timestamp = datetime.fromisoformat(start)
        end_timestamp = datetime.fromisoformat(end)
        temp_values = self.get_temp_values()
        return [
            temp_value
            for temp_value in temp_values
            if start_timestamp <= datetime.fromisoformat(temp_value[0]) <= end_timestamp
        ]

    def get_temp_sensor_tracking(self) -> list:
        """Gibt die Laufzeit des Sensors aus der Datenbank zurück.

        :return: Laufzeit des Sensors
        """
        self.cur.execute("SELECT * FROM temp_sensor_tracking")
        return self.cur.fetchall()

    def get_lambda_values(self) -> list:
        """Gibt alle Lambda-Werte aus der Datenbank zurück.

        :return: Lambda-Werte
        """
        self.cur.execute("SELECT * FROM lambda")
        return self.cur.fetchall()

    def get_lambda_values_between(self, start: str, end: str) -> list:
        """Gibt alle Lambda-Werte aus der Datenbank zwischen zwei Zeitpunkten zurück.

        :param start: Startzeitpunkt in ISO-Format
        :param end: Endzeit in ISO-Format
        :return: Lambda-Werte
        """
        start_timestamp = datetime.fromisoformat(start)
        end_timestamp = datetime.fromisoformat(end)
        lambda_values = self.get_lambda_values()
        return [
            lambda_value
            for lambda_value in lambda_values
            if start_timestamp <= datetime.fromisoformat(lambda_value[0]) <= end_timestamp
        ]

    def execute(self, query: str, args: tuple = ()):
        self.cur.execute(query, args)
        self.conn.commit()

    def __del__(self):
        self.conn.close()

    def __init_temp_values(self):
        self.execute("CREATE TABLE IF NOT EXISTS temps (timestamp TEXT PRIMARY KEY, value float)")

    def __init_temp_sensor_tracking(self):
        self.execute(
            "CREATE TABLE IF NOT EXISTS temp_sensor_tracking (id INTEGER PRIMARY KEY, time_run_in_sec integer)"
        )

        try:
            self.insert_temp_sensor_tracking(0, 0)
            self.insert_temp_sensor_tracking(1, 0)
        except sqlite3.IntegrityError:
            pass

    def __init_lambda_values(self):
        self.execute("CREATE TABLE IF NOT EXISTS lambda (timestamp TEXT PRIMARY KEY, value float)")

    def __clear_temp_values(self, older_than_days: int = 30):
        now = datetime.now()
        older_than = now - timedelta(days=older_than_days)
        older_than_str = older_than.isoformat()
        self.execute("DELETE FROM temps WHERE timestamp < ?", (older_than_str,))

    def __clear_lambda_values(self, older_than_days: int = 30):
        now = datetime.now()
        older_than = now - timedelta(days=older_than_days)
        older_than_str = older_than.isoformat()
        self.execute("DELETE FROM lambda WHERE timestamp < ?", (older_than_str,))


db_connection = Database("MAMA.sqlite")