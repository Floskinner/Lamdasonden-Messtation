import random
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from mama.models.database import db_connection


def generate_temp_data():
    now = datetime.now(tz=timezone.utc)

    print(f"Generating temp data for {now}")
    for i in range(60):
        temp = random.randint(300, 1000)
        timestamp = now - timedelta(seconds=60 - i)
        timestamp_str = timestamp.isoformat()
        sensor_id = i % 2
        db_connection.execute("INSERT INTO temps VALUES (?, ?, ?)", (sensor_id, timestamp_str, temp))


def generate_lambda_data():
    now = datetime.now(tz=timezone.utc)

    print(f"Generating lambda data for {now}")
    for i in range(60):
        lambda_value = random.random() + 0.4
        timestamp = now - timedelta(seconds=60 - i)
        timestamp_str = timestamp.isoformat()
        sensor_id = i % 2
        db_connection.execute("INSERT INTO lambda VALUES (?, ?, ?)", (sensor_id, timestamp_str, lambda_value))


if __name__ == "__main__":
    generate_temp_data()
    generate_lambda_data()
