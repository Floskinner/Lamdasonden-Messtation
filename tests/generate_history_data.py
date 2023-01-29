import random
from datetime import datetime
from datetime import timedelta

from database import db_connection


def generate_temp_data():
    now = datetime.now()
    for i in range(60):
        temp = random.randint(300, 1000)
        timestamp = now - timedelta(seconds=60 - i)
        timestamp_str = timestamp.isoformat()
        sensor_id = i % 2
        db_connection.execute("INSERT INTO temps VALUES (?, ?, ?)", (sensor_id, timestamp_str, temp))


if __name__ == "__main__":
    generate_temp_data()
