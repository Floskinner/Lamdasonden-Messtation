import sqlite3
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path
from typing import Any


class Database:
    def __init__(self, db_file: Path):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.__init_temp_values()
        self.__init_temp_sensor_tracking()
        self.__init_lambda_values()

        self.__clear_temp_values()
        self.__clear_lambda_values()

    def insert_temp_value(self, sensor_id: int, value: float):
        """Fügt einen Temperaturwert in die Datenbank mit dem Zeitstempel ein.

        :param sensor_id: Sensor ID
        :param value: Temperaturwert
        """
        timestamp_int = datetime.now(tz=timezone.utc)
        timestamp = timestamp_int.isoformat()
        self.execute("INSERT INTO temps VALUES (?, ?, ?)", (sensor_id, timestamp, value))

    def insert_temp_sensor_tracking(
        self, sensor_id: int, time_run_in_min: int, error_state: int = 0, error_message: str = ""
    ):
        """Fügt einen neuen Sensor mit entsprechender Laufzeit in die Datenbank hinzu.

        :param sensor_id: Sensor ID
        :param time_run_in_min: Laufzeit in Minuten
        :param error_state: Fehlerzustand
        :param error_message: Fehlermeldung
        """
        self.execute(
            "INSERT INTO temp_sensor_tracking VALUES (?, ?, ?, ?)",
            (sensor_id, time_run_in_min, error_state, error_message),
        )

    def insert_lambda_value(self, sensor_id: int, value: float):
        """Fügt einen Lambda-Wert in die Datenbank mit dem Zeitstempel ein.

        :param sensor_id: Sensor ID
        :param value: Lambda-Wert
        """
        timestamp_int = datetime.now(tz=timezone.utc)
        timestamp = timestamp_int.isoformat()
        self.execute("INSERT INTO lambda VALUES (?, ?, ?)", (sensor_id, timestamp, value))

    def update_temp_sensor_tracking(self, sensor_id: int, time_run_in_min: int):
        """Aktualisiert die Laufzeit des Sensors.

        :param time_run_in_min: Laufzeit in Minuten
        """
        self.execute("UPDATE temp_sensor_tracking SET time_run_in_min = ? WHERE id = ?", (time_run_in_min, sensor_id))

    def set_error_state(self, sensor_id: int, error_state: int, error_message: str):
        """Aktualisiert den Fehlerzustand des Sensors.

        :param sensor_id: Sensor ID
        :param error_state: Fehlerzustand
        :param error_message: Fehlermeldung
        """
        self.execute(
            "UPDATE temp_sensor_tracking SET error_state = ?, error_msg = ? WHERE id = ?",
            (error_state, error_message, sensor_id),
        )

    def get_error_state(self, sensor_id: int) -> tuple[int, str]:
        """Gibt den Fehlerzustand des Sensors zurück.

        :param sensor_id: Sensor ID
        :return: Fehlerzustand
        """
        cur = self.conn.cursor()
        cur.execute("SELECT error_state, error_msg FROM temp_sensor_tracking WHERE id = ?", (sensor_id,))
        result = cur.fetchone()
        cur.close()
        return result

    def reset_error_state(self, sensor_id: int):
        """Setzt den Fehlerzustand des Sensors zurück.

        :param sensor_id: Sensor ID
        """
        self.execute("UPDATE temp_sensor_tracking SET error_state = 0, error_msg = '' WHERE id = ?", (sensor_id,))

    def get_temp_values(self) -> list:
        """Gibt alle Temperaturwerte aus der Datenbank zurück.

        :return: Temperaturwerte
        """
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM temps")
        result = cur.fetchall()
        cur.close()
        return result

    def get_temp_values_between(self, start: str, end: str) -> list:
        """Gibt alle Temperaturwerte aus der Datenbank zwischen zwei Zeitpunkten zurück.

        :param start: Startzeitpunkt in ISO-Format
        :param end: Endzeit in ISO-Format
        :return: Temperaturwerte
        """
        start_timestamp = datetime.fromisoformat(start)
        end_timestamp = datetime.fromisoformat(end)
        temp_values = self.get_temp_values()  # type: list
        return [
            temp_value
            for temp_value in temp_values
            if start_timestamp <= datetime.fromisoformat(temp_value[1]) <= end_timestamp
        ]

    def get_temp_sensor_tracking(self, sensor_id: int) -> Any:
        """Gibt die Laufzeit des Sensors aus der Datenbank zurück.

        :return: Laufzeit des Sensors
        """
        cur = self.conn.cursor()
        cur.execute("SELECT time_run_in_min FROM temp_sensor_tracking WHERE id = ?", (sensor_id,))
        result = cur.fetchone()
        cur.close()
        return result

    def get_lambda_values(self) -> list:
        """Gibt alle Lambda-Werte aus der Datenbank zurück.

        :return: Lambda-Werte
        """
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM lambda")
        result = cur.fetchall()
        cur.close()
        return result

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
            if start_timestamp <= datetime.fromisoformat(lambda_value[1]) <= end_timestamp
        ]

    def execute(self, query: str, args: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(query, args)
        self.conn.commit()
        cur.close()

    def __del__(self):
        self.conn.close()

    def __init_temp_values(self):
        self.execute("CREATE TABLE IF NOT EXISTS temps (sensorid integer, timestamp TEXT, value float)")

    def __init_temp_sensor_tracking(self):
        self.execute(
            'CREATE TABLE IF NOT EXISTS temp_sensor_tracking (id INTEGER PRIMARY KEY, time_run_in_min integer, error_state integer DEFAULT FALSE, error_msg TEXT DEFAULT " ")'  # noqa: E501
        )

        try:
            self.insert_temp_sensor_tracking(0, 0)
            self.insert_temp_sensor_tracking(1, 0)
        except sqlite3.IntegrityError:
            pass

    def __init_lambda_values(self):
        self.execute("CREATE TABLE IF NOT EXISTS lambda (sensorid integer, timestamp TEXT, value float)")

    def __clear_temp_values(self, older_than_days: int = 30):
        now = datetime.now(tz=timezone.utc)
        older_than = now - timedelta(days=older_than_days)
        older_than_str = older_than.isoformat()
        self.execute("DELETE FROM temps WHERE timestamp < ?", (older_than_str,))

    def __clear_lambda_values(self, older_than_days: int = 30):
        now = datetime.now(tz=timezone.utc)
        older_than = now - timedelta(days=older_than_days)
        older_than_str = older_than.isoformat()
        self.execute("DELETE FROM lambda WHERE timestamp < ?", (older_than_str,))


# Get the project root directory (4 levels up from this file)
_project_root = Path(__file__).parent.parent.parent
db_connection = Database(_project_root / "MAMA.sqlite")
